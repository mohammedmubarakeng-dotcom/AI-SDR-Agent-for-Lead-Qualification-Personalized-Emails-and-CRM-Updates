"""
Load leads from CSV files.
"""

import pandas as pd
from typing import List
from src.models import Lead
from src.database import save_lead, log_activity


def load_leads_from_csv(csv_path: str) -> List[Lead]:
    """Load leads from a CSV file and save them to the database."""
    df = pd.read_csv(csv_path)

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    leads = []
    for _, row in df.iterrows():
        lead = Lead(
            lead_id=str(row.get("lead_id", "")),
            first_name=str(row.get("first_name", "")),
            last_name=str(row.get("last_name", "")),
            email=str(row.get("email", "")),
            job_title=str(row.get("job_title", "")),
            company_name=str(row.get("company_name", "")),
            company_size=int(row.get("company_size", 0)),
            industry=str(row.get("industry", "")),
            website=str(row.get("website", "")),
            linkedin_url=str(row.get("linkedin_url", "")),
            lead_source=str(row.get("lead_source", "")),
            notes=str(row.get("notes", "")),
        )
        leads.append(lead)
        save_lead(lead)
        log_activity(lead.lead_id, "LEAD_IMPORTED", f"Imported from {csv_path}")

    return leads