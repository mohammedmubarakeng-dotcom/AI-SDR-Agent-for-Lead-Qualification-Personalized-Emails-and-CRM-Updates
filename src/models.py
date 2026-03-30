"""
Data models for the SDR Agent system.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Lead:
    lead_id: str
    first_name: str
    last_name: str
    email: str
    job_title: str
    company_name: str
    company_size: int
    industry: str
    website: str = ""
    linkedin_url: str = ""
    lead_source: str = ""
    notes: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"Name: {self.full_name}\n"
            f"Title: {self.job_title}\n"
            f"Company: {self.company_name}\n"
            f"Company Size: {self.company_size} employees\n"
            f"Industry: {self.industry}\n"
            f"Website: {self.website}\n"
            f"LinkedIn: {self.linkedin_url}\n"
            f"Lead Source: {self.lead_source}\n"
            f"Notes: {self.notes}"
        )


@dataclass
class LeadQualification:
    lead_id: str
    score: int  # 0-100
    tier: str  # hot, warm, cold
    reasoning: str
    icp_match_details: str
    buying_signals: str
    personalized_email_subject: str = ""
    personalized_email_body: str = ""
    follow_up_email_subject: str = ""
    follow_up_email_body: str = ""
    crm_note: str = ""
    next_best_action: str = ""
    processed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    email_sent: bool = False
    email_status: str = ""

    def to_dict(self) -> dict:
        return asdict(self)