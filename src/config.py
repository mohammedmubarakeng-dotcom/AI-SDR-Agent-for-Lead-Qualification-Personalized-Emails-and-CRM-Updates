"""
Configuration for the AI SDR Agent.
Loads environment variables and defines ICP (Ideal Customer Profile).
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# --- API Keys ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "hamikabaher1999@gmail.com")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER")
PUSHOVER_TOKEN = os.environ.get("PUSHOVER_TOKEN")

# --- Model Configuration ---
# Using free Groq models
PRIMARY_MODEL = "llama-3.3-70b-versatile"
FAST_MODEL = "llama-3.1-8b-instant"

# --- Ideal Customer Profile (ICP) ---
ICP = {
    "target_industries": [
        "SaaS / Cloud Computing",
        "FinTech / AI",
        "HealthTech / Telemedicine",
        "EdTech / SaaS",
        "Cloud Infrastructure / MSP",
        "Cybersecurity",
        "Banking / Financial Services",
    ],
    "target_titles": [
        "CEO", "CTO", "CIO", "CISO", "CFO",
        "VP of Engineering", "VP of Product", "VP of Sales",
        "Head of Compliance", "Head of Operations",
        "Director of Engineering", "IT Director",
        "Founder", "Co-founder",
        "Chief Technology Officer", "Chief Information Security Officer",
    ],
    "company_size": {
        "min": 20,
        "max": 5000,
        "ideal_min": 50,
        "ideal_max": 500,
    },
    "signals": [
        "Recently raised funding",
        "Hiring for security/compliance roles",
        "Handles sensitive data (health, financial, student)",
        "Works with enterprise clients",
        "Needs SOC2/HIPAA/GDPR compliance",
        "Experienced data breach",
        "Using manual compliance processes",
        "Expressed interest in our product",
    ],
    "company_description": (
        "ComplAI is a SaaS platform that automates SOC2 compliance "
        "and audit preparation using AI. We help companies get audit-ready "
        "in weeks instead of months, reducing manual work by 80%."
    ),
}

# --- Database ---
DATABASE_PATH = "sdr_crm.db"

# --- CSV ---
DEFAULT_CSV_PATH = "data/sample_leads.csv"