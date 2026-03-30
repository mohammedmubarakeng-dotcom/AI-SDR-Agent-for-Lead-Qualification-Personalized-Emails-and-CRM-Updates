"""
Gradio dashboard for the AI SDR Agent.
Shows leads, qualifications, stats, and allows running the pipeline.

Usage:
    python dashboard/app.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
import pandas as pd
import asyncio
import tempfile
import shutil

from src.database import (
    init_database,
    get_all_leads,
    get_all_qualifications,
    get_dashboard_stats,
    get_activity_log,
)
from src.pipeline import run_full_pipeline
from src.config import DEFAULT_CSV_PATH


# ============================================================
# Helper functions
# ============================================================

def get_stats_html():
    """Generate HTML stats cards."""
    stats = get_dashboard_stats()
    return f"""
    <div style="display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 20px;">
        <div style="flex:1; min-width:140px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 32px; font-weight: bold;">{stats['total_leads']}</div>
            <div style="font-size: 14px; opacity: 0.9;">Total Leads</div>
        </div>
        <div style="flex:1; min-width:140px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 20px; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 32px; font-weight: bold;">{stats['total_qualified']}</div>
            <div style="font-size: 14px; opacity: 0.9;">Qualified</div>
        </div>
        <div style="flex:1; min-width:140px; background: linear-gradient(135deg, #ff5858 0%, #f09819 100%);
                    padding: 20px; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 32px; font-weight: bold;">{stats['hot']}</div>
            <div style="font-size: 14px; opacity: 0.9;">🔥 Hot Leads</div>
        </div>
        <div style="flex:1; min-width:140px; background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
                    padding: 20px; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 32px; font-weight: bold;">{stats['warm']}</div>
            <div style="font-size: 14px; opacity: 0.9;">🟡 Warm Leads</div>
        </div>
        <div style="flex:1; min-width:140px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    padding: 20px; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 32px; font-weight: bold;">{stats['cold']}</div>
            <div style="font-size: 14px; opacity: 0.9;">🔵 Cold Leads</div>
        </div>
        <div style="flex:1; min-width:140px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                    padding: 20px; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 32px; font-weight: bold;">{stats['avg_score']}</div>
            <div style="font-size: 14px; opacity: 0.9;">📈 Avg Score</div>
        </div>
        <div style="flex:1; min-width:140px; background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);
                    padding: 20px; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 32px; font-weight: bold;">{stats['emails_sent']}</div>
            <div style="font-size: 14px; opacity: 0.9;">✉️ Emails Sent</div>
        </div>
    </div>
    """


def get_leads_df():
    """Get leads as a DataFrame."""
    leads = get_all_leads()
    if not leads:
        return pd.DataFrame(columns=["lead_id", "first_name", "last_name", "email",
                                      "job_title", "company_name", "company_size", "industry"])
    df = pd.DataFrame(leads)
    cols = ["lead_id", "first_name", "last_name", "email", "job_title",
            "company_name", "company_size", "industry", "lead_source"]
    return df[[c for c in cols if c in df.columns]]


def get_qualifications_df():
    """Get qualifications as a DataFrame."""
    quals = get_all_qualifications()
    if not quals:
        return pd.DataFrame(columns=["lead_id", "first_name", "last_name",
                                      "company_name", "score", "tier"])
    df = pd.DataFrame(quals)

    # Add emoji to tier
    tier_emoji = {"hot": "🔥 Hot", "warm": "🟡 Warm", "cold": "🔵 Cold"}
    if "tier" in df.columns:
        df["tier_display"] = df["tier"].map(tier_emoji).fillna(df["tier"])

    cols = ["lead_id", "first_name", "last_name", "company_name", "job_title",
            "score", "tier_display", "reasoning", "next_best_action",
            "personalized_email_subject", "personalized_email_body"]
    return df[[c for c in cols if c in df.columns]]


def get_activity_df():
    """Get activity log as a DataFrame."""
    activities = get_activity_log()
    if not activities:
        return pd.DataFrame(columns=["timestamp", "lead_id", "first_name",
                                      "last_name", "action", "details"])
    df = pd.DataFrame(activities)
    cols = ["timestamp", "lead_id", "first_name", "last_name",
            "company_name", "action", "details"]
    return df[[c for c in cols if c in df.columns]]


def get_lead_detail(lead_id: str):
    """Get detailed view of a specific lead's qualification."""
    quals = get_all_qualifications()
    for q in quals:
        if q["lead_id"] == lead_id:
            tier_emoji = {"hot": "🔥", "warm": "🟡", "cold": "🔵"}.get(q.get("tier", ""), "")
            detail = f"""
## {q.get('first_name', '')} {q.get('last_name', '')} — {q.get('company_name', '')}

**Title:** {q.get('job_title', '')}
**Industry:** {q.get('industry', '')}
**Company Size:** {q.get('company_size', '')} employees

---

### Qualification Score: {q.get('score', 0)}/100 {tier_emoji} {q.get('tier', '').upper()}

**Reasoning:** {q.get('reasoning', '')}

**ICP Match:** {q.get('icp_match_details', '')}

**Buying Signals:** {q.get('buying_signals', '')}

---

### 📧 Best Outreach Email

**Subject:** {q.get('personalized_email_subject', 'N/A')}

{q.get('personalized_email_body', 'No email generated (cold lead).')}

---

### 📬 Follow-up Email

**Subject:** {q.get('follow_up_email_subject', 'N/A')}

{q.get('follow_up_email_body', 'No follow-up generated.')}

---

### 📋 CRM Note
{q.get('crm_note', '')}

### ➡️ Next Best Action
{q.get('next_best_action', '')}
"""
            return detail
    return "Lead not found. Please run the pipeline first."


def get_lead_ids():
    """Get list of lead IDs for dropdown."""
    quals = get_all_qualifications()
    if not quals:
        leads = get_all_leads()
        return [l["lead_id"] for l in leads] if leads else ["No leads yet"]
    return [f"{q['lead_id']} — {q.get('first_name', '')} {q.get('last_name', '')} ({q.get('company_name', '')})" for q in quals]


# ============================================================
# Pipeline runner for Gradio
# ============================================================

def run_pipeline_from_ui(csv_file, send_email, send_notif, max_leads_str):
    """Run the pipeline from the Gradio UI."""
    # Determine CSV path
    if csv_file is not None:
        csv_path = csv_file.name
    else:
        csv_path = DEFAULT_CSV_PATH

    max_leads = int(max_leads_str) if max_leads_str and max_leads_str.strip() else None

    try:
        results = asyncio.run(
            run_full_pipeline(
                csv_path=csv_path,
                send_email=send_email,
                send_notification=send_notif,
                max_leads=max_leads,
            )
        )
        hot = sum(1 for r in results if r.tier == "hot")
        warm = sum(1 for r in results if r.tier == "warm")
        cold = sum(1 for r in results if r.tier == "cold")
        avg = sum(r.score for r in results) / len(results) if results else 0

        summary = f"""
## ✅ Pipeline Complete!

**Leads Processed:** {len(results)}
**🔥 Hot:** {hot} | **🟡 Warm:** {warm} | **🔵 Cold:** {cold}
**📈 Average Score:** {avg:.1f}/100

### Top Leads:
"""
        for r in sorted(results, key=lambda x: x.score, reverse=True)[:5]:
            emoji = {"hot": "🔥", "warm": "🟡", "cold": "🔵"}.get(r.tier, "")
            summary += f"- **{r.lead_id}** — Score: {r.score} {emoji} {r.tier.upper()}\n"

        return summary

    except Exception as e:
        return f"## ❌ Error\n\n```\n{str(e)}\n```"


# ============================================================
# Build the Gradio app
# ============================================================

def create_dashboard():
    init_database()

    with gr.Blocks(
        title="AI SDR Agent Dashboard",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container { max-width: 1400px !important; }
        """
    ) as app:

        gr.Markdown("""
        # 🤖 AI SDR Agent Dashboard
        ### Lead Qualification, Personalized Emails & CRM — Powered by Groq + OpenAI Agents SDK
        """)

        # --- Tab: Overview ---
        with gr.Tab("📊 Overview"):
            stats_html = gr.HTML(value=get_stats_html())
            refresh_btn = gr.Button("🔄 Refresh Stats", variant="secondary")
            refresh_btn.click(fn=get_stats_html, outputs=stats_html)

            gr.Markdown("### 📋 Qualified Leads (sorted by score)")
            quals_table = gr.Dataframe(
                value=get_qualifications_df(),
                interactive=False,
                wrap=True,
            )
            refresh_quals_btn = gr.Button("🔄 Refresh Table")
            refresh_quals_btn.click(fn=get_qualifications_df, outputs=quals_table)

        # --- Tab: Lead Detail ---
        with gr.Tab("🔍 Lead Detail"):
            gr.Markdown("### Select a lead to see full qualification details")
            lead_dropdown = gr.Dropdown(
                choices=get_lead_ids(),
                label="Select Lead",
                interactive=True,
            )
            refresh_dropdown_btn = gr.Button("🔄 Refresh List")
            lead_detail_md = gr.Markdown("Select a lead above to see details.")

            def show_detail(selected):
                if not selected or selected == "No leads yet":
                    return "No lead selected."
                lid = selected.split(" — ")[0].strip()
                return get_lead_detail(lid)

            lead_dropdown.change(fn=show_detail, inputs=lead_dropdown, outputs=lead_detail_md)
            refresh_dropdown_btn.click(
                fn=get_lead_ids,
                outputs=lead_dropdown,
            )

        # --- Tab: Run Pipeline ---
        with gr.Tab("🚀 Run Pipeline"):
            gr.Markdown("""
            ### Run the AI SDR Pipeline
            Upload a CSV or use the default sample leads.
            The AI will research, qualify, and write personalized emails for each lead.
            """)

            with gr.Row():
                csv_upload = gr.File(label="Upload Leads CSV (optional)", file_types=[".csv"])
                with gr.Column():
                    send_email_check = gr.Checkbox(label="📧 Send emails via SendGrid", value=False)
                    send_notif_check = gr.Checkbox(label="🔔 Send Pushover notifications for hot leads", value=False)
                    max_leads_input = gr.Textbox(label="Max leads to process (blank = all)", value="3", placeholder="e.g., 5")

            run_btn = gr.Button("🚀 Run Pipeline", variant="primary", size="lg")
            pipeline_output = gr.Markdown("Pipeline results will appear here...")

            run_btn.click(
                fn=run_pipeline_from_ui,
                inputs=[csv_upload, send_email_check, send_notif_check, max_leads_input],
                outputs=pipeline_output,
            )

        # --- Tab: All Leads ---
        with gr.Tab("📁 All Leads"):
            leads_table = gr.Dataframe(value=get_leads_df(), interactive=False, wrap=True)
            refresh_leads_btn = gr.Button("🔄 Refresh")
            refresh_leads_btn.click(fn=get_leads_df, outputs=leads_table)

        # --- Tab: Activity Log ---
        with gr.Tab("📜 Activity Log"):
            activity_table = gr.Dataframe(value=get_activity_df(), interactive=False, wrap=True)
            refresh_activity_btn = gr.Button("🔄 Refresh")
            refresh_activity_btn.click(fn=get_activity_df, outputs=activity_table)

        # --- Tab: About ---
        with gr.Tab("ℹ️ About"):
            gr.Markdown("""
            ## AI SDR Agent for Lead Qualification, Personalized Emails & CRM Updates

            ### Architecture
            This project uses the **OpenAI Agents SDK** with **Groq** (Llama 3.3 70B) as the LLM backend.

            **8 Specialized Agents collaborate:**
            1. 🔬 **Lead Research Analyst** — Researches company & lead
            2. 📊 **Lead Qualification Specialist** — Scores & classifies leads (Hot/Warm/Cold)
            3. ✍️ **Professional Email Writer** — Formal outreach style
            4. 🎨 **Engaging Email Writer** — Witty, creative style
            5. ⚡ **Concise Email Writer** — Short, direct style
            6. 🏆 **Email Selection Expert** — Picks the best email draft
            7. 📬 **Follow-up Email Writer** — Creates follow-up sequences
            8. 🎯 **SDR Manager** — Orchestrates the entire pipeline

            ### Tech Stack
            - **LLM:** Groq (Llama 3.3 70B Versatile + Llama 3.1 8B Instant)
            - **Agent Framework:** OpenAI Agents SDK
            - **Email:** SendGrid API
            - **Notifications:** Pushover API
            - **Database:** SQLite (CRM)
            - **Dashboard:** Gradio
            - **Language:** Python

            ### Features
            - ✅ CSV lead import
            - ✅ AI-powered lead research
            - ✅ ICP-based lead scoring (0-100)
            - ✅ Hot / Warm / Cold classification
            - ✅ 3 competing email drafts → best one selected
            - ✅ Follow-up email generation
            - ✅ CRM notes & activity logging
            - ✅ SendGrid email delivery
            - ✅ Pushover push notifications
            - ✅ Interactive dashboard

            ---
            Built following the **Ed Donner Agentic AI Course** (Week 2, Day 2) pattern.
            """)

    return app


if __name__ == "__main__":
    app = create_dashboard()
    app.launch(share=False)