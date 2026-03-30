"""
Main pipeline: loads leads, runs each through the SDR Manager agent,
parses results, saves to DB, optionally sends email & push notification.
"""

import asyncio
import re
import os
from typing import List, Optional

from agents import Runner, trace

from src.config import DATABASE_PATH
from src.models import Lead, LeadQualification
from src.database import (
    init_database,
    save_lead,
    save_qualification,
    log_activity,
)
from src.lead_loader import load_leads_from_csv
from src.agents import sdr_manager
from src.tools import send_outreach_email, send_pushover_notification

# Ensure Groq backend is set
os.environ.setdefault("OPENAI_API_KEY", os.environ.get("GROQ_API_KEY", ""))
os.environ.setdefault("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")


# ============================================================
# Parse the agent output into a LeadQualification object
# ============================================================

def _extract(text: str, label: str, default: str = "") -> str:
    """Pull the value after a label like 'SCORE: 85'."""
    pattern = rf"{label}:\s*(.+?)(?:\n[A-Z_]+:|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return default


def parse_agent_output(lead_id: str, raw: str) -> LeadQualification:
    """Parse the SDR Manager's final report into a LeadQualification."""
    score_str = _extract(raw, "SCORE", "0")
    try:
        score = int(re.search(r"\d+", score_str).group())
    except (AttributeError, ValueError):
        score = 0

    tier = _extract(raw, "TIER", "cold").lower().strip()
    if tier not in ("hot", "warm", "cold"):
        if score >= 75:
            tier = "hot"
        elif score >= 45:
            tier = "warm"
        else:
            tier = "cold"

    return LeadQualification(
        lead_id=lead_id,
        score=score,
        tier=tier,
        reasoning=_extract(raw, "REASONING"),
        icp_match_details=_extract(raw, "ICP_MATCH"),
        buying_signals=_extract(raw, "BUYING_SIGNALS"),
        personalized_email_subject=_extract(raw, "BEST_EMAIL_SUBJECT"),
        personalized_email_body=_extract(raw, "BEST_EMAIL_BODY"),
        follow_up_email_subject=_extract(raw, "FOLLOW_UP_SUBJECT"),
        follow_up_email_body=_extract(raw, "FOLLOW_UP_BODY"),
        crm_note=_extract(raw, "CRM_NOTE"),
        next_best_action=_extract(raw, "NEXT_ACTION"),
    )


# ============================================================
# Process a single lead
# ============================================================

async def process_lead(
    lead: Lead,
    send_email: bool = False,
    send_notification: bool = False,
) -> LeadQualification:
    """Run one lead through the full SDR agent pipeline."""

    log_activity(lead.lead_id, "PIPELINE_START", f"Processing {lead.full_name}")

    prompt = (
        f"Process this lead through the full SDR pipeline:\n\n"
        f"Lead ID: {lead.lead_id}\n"
        f"{lead.summary()}"
    )

    with trace(f"SDR Pipeline — {lead.full_name}"):
        result = await Runner.run(sdr_manager, prompt)

    raw_output = result.final_output
    qual = parse_agent_output(lead.lead_id, raw_output)

    # Persist
    save_qualification(qual)
    log_activity(lead.lead_id, "QUALIFICATION_COMPLETE",
                 f"Score: {qual.score} | Tier: {qual.tier}")

    # Optionally send email for hot / warm leads
    if send_email and qual.tier in ("hot", "warm") and qual.personalized_email_body:
        email_result = send_outreach_email.invoke(
            None,  # context
            lead_id=lead.lead_id,
            to_email=lead.email,
            subject=qual.personalized_email_subject,
            html_body=f"<div style='font-family:Arial,sans-serif'>{qual.personalized_email_body}</div>",
        )
        # function_tool returns a string (JSON), handle gracefully
        if isinstance(email_result, dict):
            qual.email_sent = email_result.get("status") == "success"
            qual.email_status = email_result.get("message", "")
        else:
            qual.email_sent = "success" in str(email_result).lower()
            qual.email_status = str(email_result)

    # Optionally push notification
    if send_notification and qual.tier == "hot":
        send_pushover_notification.invoke(
            None,
            title=f"🔥 Hot Lead: {lead.full_name}",
            message=(
                f"Score: {qual.score}/100\n"
                f"Company: {lead.company_name}\n"
                f"Title: {lead.job_title}\n"
                f"Next: {qual.next_best_action}"
            ),
        )

    return qual


# ============================================================
# Process a batch of leads
# ============================================================

async def process_leads(
    leads: List[Lead],
    send_email: bool = False,
    send_notification: bool = False,
) -> List[LeadQualification]:
    """Run multiple leads through the pipeline sequentially.
    (Sequential to respect Groq rate limits on free tier.)
    """
    results = []
    for i, lead in enumerate(leads):
        print(f"\n{'='*60}")
        print(f"Processing lead {i+1}/{len(leads)}: {lead.full_name} @ {lead.company_name}")
        print(f"{'='*60}")
        try:
            qual = await process_lead(lead, send_email, send_notification)
            results.append(qual)
            print(f"  ✅ Score: {qual.score}/100 | Tier: {qual.tier.upper()}")
            print(f"  📝 {qual.reasoning[:100]}...")
            if qual.personalized_email_subject:
                print(f"  ✉️  Email: {qual.personalized_email_subject}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            # Create a fallback qualification
            fallback = LeadQualification(
                lead_id=lead.lead_id,
                score=0,
                tier="cold",
                reasoning=f"Error during processing: {str(e)}",
                icp_match_details="",
                buying_signals="",
                crm_note=f"Processing error: {str(e)}",
                next_best_action="Retry processing",
            )
            save_qualification(fallback)
            results.append(fallback)

        # Small delay to respect Groq rate limits
        if i < len(leads) - 1:
            print("  ⏳ Waiting 3 seconds (rate limit)...")
            await asyncio.sleep(3)

    return results


# ============================================================
# Full pipeline entry point
# ============================================================

async def run_full_pipeline(
    csv_path: str,
    send_email: bool = False,
    send_notification: bool = False,
    max_leads: Optional[int] = None,
) -> List[LeadQualification]:
    """Complete pipeline: load CSV → process all leads → return results."""

    print("🚀 AI SDR Agent Pipeline Starting...")
    print(f"📂 Loading leads from: {csv_path}")

    init_database()
    leads = load_leads_from_csv(csv_path)

    if max_leads:
        leads = leads[:max_leads]

    print(f"📊 Loaded {len(leads)} leads")
    print(f"📧 Email sending: {'ON' if send_email else 'OFF'}")
    print(f"🔔 Push notifications: {'ON' if send_notification else 'OFF'}")

    results = await process_leads(leads, send_email, send_notification)

    # Summary
    hot = sum(1 for r in results if r.tier == "hot")
    warm = sum(1 for r in results if r.tier == "warm")
    cold = sum(1 for r in results if r.tier == "cold")
    avg_score = sum(r.score for r in results) / len(results) if results else 0

    print(f"\n{'='*60}")
    print("📊 PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"Total Leads Processed: {len(results)}")
    print(f"🔥 Hot:  {hot}")
    print(f"🟡 Warm: {warm}")
    print(f"🔵 Cold: {cold}")
    print(f"📈 Average Score: {avg_score:.1f}/100")
    print(f"{'='*60}")

    return results