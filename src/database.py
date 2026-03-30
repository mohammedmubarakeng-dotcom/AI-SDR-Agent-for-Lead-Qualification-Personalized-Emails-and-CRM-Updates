"""
SQLite CRM database for storing leads and qualification results.
"""

import sqlite3
import json
from typing import List, Optional
from src.config import DATABASE_PATH
from src.models import Lead, LeadQualification


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            lead_id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            job_title TEXT,
            company_name TEXT,
            company_size INTEGER,
            industry TEXT,
            website TEXT,
            linkedin_url TEXT,
            lead_source TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qualifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id TEXT,
            score INTEGER,
            tier TEXT,
            reasoning TEXT,
            icp_match_details TEXT,
            buying_signals TEXT,
            personalized_email_subject TEXT,
            personalized_email_body TEXT,
            follow_up_email_subject TEXT,
            follow_up_email_body TEXT,
            crm_note TEXT,
            next_best_action TEXT,
            processed_at TEXT,
            email_sent BOOLEAN DEFAULT 0,
            email_status TEXT DEFAULT '',
            FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id TEXT,
            action TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_lead(lead: Lead):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO leads
        (lead_id, first_name, last_name, email, job_title,
         company_name, company_size, industry, website,
         linkedin_url, lead_source, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead.lead_id, lead.first_name, lead.last_name, lead.email,
        lead.job_title, lead.company_name, lead.company_size,
        lead.industry, lead.website, lead.linkedin_url,
        lead.lead_source, lead.notes
    ))
    conn.commit()
    conn.close()


def save_qualification(qual: LeadQualification):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO qualifications
        (lead_id, score, tier, reasoning, icp_match_details,
         buying_signals, personalized_email_subject, personalized_email_body,
         follow_up_email_subject, follow_up_email_body,
         crm_note, next_best_action, processed_at, email_sent, email_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        qual.lead_id, qual.score, qual.tier, qual.reasoning,
        qual.icp_match_details, qual.buying_signals,
        qual.personalized_email_subject, qual.personalized_email_body,
        qual.follow_up_email_subject, qual.follow_up_email_body,
        qual.crm_note, qual.next_best_action, qual.processed_at,
        qual.email_sent, qual.email_status
    ))
    conn.commit()
    conn.close()


def log_activity(lead_id: str, action: str, details: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO activity_log (lead_id, action, details)
        VALUES (?, ?, ?)
    """, (lead_id, action, details))
    conn.commit()
    conn.close()


def get_all_leads() -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_qualifications() -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT q.*, l.first_name, l.last_name, l.company_name,
               l.job_title, l.industry, l.email, l.company_size
        FROM qualifications q
        JOIN leads l ON q.lead_id = l.lead_id
        ORDER BY q.score DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_activity_log() -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, l.first_name, l.last_name, l.company_name
        FROM activity_log a
        JOIN leads l ON a.lead_id = l.lead_id
        ORDER BY a.timestamp DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_dashboard_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM leads")
    total_leads = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM qualifications")
    total_qualified = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM qualifications WHERE tier = 'hot'")
    hot = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM qualifications WHERE tier = 'warm'")
    warm = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM qualifications WHERE tier = 'cold'")
    cold = cursor.fetchone()["total"]

    cursor.execute("SELECT AVG(score) as avg_score FROM qualifications")
    avg_row = cursor.fetchone()
    avg_score = round(avg_row["avg_score"], 1) if avg_row["avg_score"] else 0

    cursor.execute("SELECT COUNT(*) as total FROM qualifications WHERE email_sent = 1")
    emails_sent = cursor.fetchone()["total"]

    conn.close()

    return {
        "total_leads": total_leads,
        "total_qualified": total_qualified,
        "hot": hot,
        "warm": warm,
        "cold": cold,
        "avg_score": avg_score,
        "emails_sent": emails_sent,
    }