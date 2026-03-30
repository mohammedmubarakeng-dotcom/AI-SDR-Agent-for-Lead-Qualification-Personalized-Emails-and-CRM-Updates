"""
Tools for the SDR Agent system.
Uses SendGrid for email, Pushover for notifications, and SQLite for CRM.
"""

import os
import json
import sendgrid
import httpx
from sendgrid.helpers.mail import Mail, Email, To, Content
from agents import function_tool
from typing import Dict
from src.config import SENDGRID_API_KEY, SENDER_EMAIL, PUSHOVER_USER, PUSHOVER_TOKEN
from src.database import log_activity


@function_tool
def send_outreach_email(lead_id: str, to_email: str, subject: str, html_body: str) -> Dict[str, str]:
    """
    Send a personalized outreach email to a lead via SendGrid.
    Args:
        lead_id: The lead ID for tracking
        to_email: The recipient email address
        subject: The email subject line
        html_body: The HTML body of the email
    Returns:
        A dict with status and message
    """
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        from_email = Email(SENDER_EMAIL)
        to_email_obj = To(to_email)
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email_obj, subject, content).get()
        response = sg.client.mail.send.post(request_body=mail)

        log_activity(lead_id, "EMAIL_SENT", f"Subject: {subject} | Status: {response.status_code}")

        return {
            "status": "success",
            "status_code": str(response.status_code),
            "message": f"Email sent to {to_email} with subject: {subject}"
        }
    except Exception as e:
        log_activity(lead_id, "EMAIL_FAILED", str(e))
        return {"status": "error", "message": str(e)}


@function_tool
def send_pushover_notification(title: str, message: str) -> Dict[str, str]:
    """
    Send a push notification to the sales rep via Pushover.
    Args:
        title: Notification title
        message: Notification message body
    Returns:
        A dict with status
    """
    try:
        response = httpx.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_TOKEN,
                "user": PUSHOVER_USER,
                "title": title,
                "message": message,
            },
        )
        return {"status": "success", "response": str(response.status_code)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@function_tool
def save_crm_note(lead_id: str, note: str) -> Dict[str, str]:
    """
    Save a CRM note for a lead in the activity log.
    Args:
        lead_id: The lead ID
        note: The CRM note content
    Returns:
        A dict with status
    """
    try:
        log_activity(lead_id, "CRM_NOTE", note)
        return {"status": "success", "message": f"CRM note saved for lead {lead_id}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@function_tool
def lookup_company_info(company_name: str, website: str, industry: str, company_size: int, notes: str) -> str:
    """
    Research company information. In production this would call Clearbit/Apollo API.
    For now it enriches based on available data.
    Args:
        company_name: Name of the company
        website: Company website URL
        industry: Industry vertical
        company_size: Number of employees
        notes: Any existing notes about the lead
    Returns:
        A string summary of company research
    """
    research = f"""
Company Research Report for {company_name}:
- Website: {website}
- Industry: {industry}
- Company Size: {company_size} employees
- Size Category: {"Startup" if company_size < 50 else "SMB" if company_size < 200 else "Mid-Market" if company_size < 1000 else "Enterprise"}
- Intelligence Notes: {notes}
- Estimated Annual Revenue: {"<$5M" if company_size < 50 else "$5M-$25M" if company_size < 200 else "$25M-$100M" if company_size < 1000 else "$100M+"}
- Likely Compliance Needs: {"Basic" if company_size < 50 else "SOC2 Type I" if company_size < 200 else "SOC2 Type II + Additional" if company_size < 1000 else "Full Enterprise Compliance Suite"}
"""
    return research