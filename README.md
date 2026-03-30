# 🤖 AI SDR Agent — Lead Qualification, Personalized Outreach & CRM Updates

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange?style=flat-square" alt="Groq">
  <img src="https://img.shields.io/badge/Framework-OpenAI%20Agents%20SDK-green?style=flat-square" alt="Agents SDK">
  <img src="https://img.shields.io/badge/Dashboard-Gradio-purple?style=flat-square" alt="Gradio">
</p>

<p align="center">
  <strong>A production-ready AI SDR Agent that helps sales teams qualify leads, generate highly personalized cold emails, create follow-ups, and log everything into a lightweight CRM (SQLite) — with a clean dashboard to review results.</strong>
</p>

<p align="center">
  Built using an <strong>agentic workflow</strong> (multi-agent collaboration + tools) inspired by Ed Donner’s Agentic AI course (Week 2 Day 2 pattern: workflow → tools → manager/orchestrator).
</p>

---

## 📸 Dashboard Preview

| Overview | Lead Detail | Run Pipeline |

*The Gradio dashboard includes: Overview stats, Lead Detail viewer, Pipeline runner, All Leads table, Activity Log, and About sections.*

---

## 🎯 What This Solves (Client Value)

Sales teams lose time and pipeline because:
- **Leads aren't qualified consistently** — reps apply different criteria
- **Reps spend hours researching** + writing similar emails manually
- **Follow-ups get missed** — no systematic tracking
- **CRM notes are incomplete or outdated** — administrative burden

This project automates that workflow while keeping **human control** over outreach.

### Typical Outcomes:
- ⚡ **Faster lead qualification** (minutes instead of hours)
- 🎯 **More consistent messaging** and follow-up quality  
- 📝 **Cleaner CRM notes** and next-step recommendations
- 💰 **Higher personalization** without manual research overhead

---

## ✨ Key Features

### Lead Intake
- Import leads from **CSV** (Apollo exports / form submissions / Google Sheets)
- Standardized lead schema (name, title, company size, industry, notes)
- Automatic database initialization

### AI Research + Qualification
- **"Company research"** enrichment tool (mock enrichment now; easily upgraded to Clearbit/Apollo)
- **ICP-based scoring 0–100** — objective, consistent qualification
- **Lead tiers**: 🔥 Hot / 🟡 Warm / 🔵 Cold
- Clear **reasoning** + detected **buying signals**
- "Next Best Action" recommendations

### Personalized Outreach
- Generates **3 different email drafts** (Professional / Engaging / Concise styles)
- Uses an AI **"picker" agent** to select the best draft for response probability
- Generates a **follow-up email** (3 days later angle)
- Subject line optimization

### CRM + Activity Logging
- Saves qualification results, CRM note, and actions into **SQLite**
- Complete **activity log**: lead imported, qualified, email status, notes, etc.
- Audit trail for compliance

### Dashboard
- 📊 **Overview**: Stats cards (Total leads, Hot/Warm/Cold counts, Avg score, Emails sent)
- 🔍 **Lead Detail**: Drill into per-lead details (score, reasoning, emails, next steps)
- 🚀 **Run Pipeline**: Upload CSV and run the pipeline directly from the UI
- 📁 **All Leads**: Browse all imported leads
- 📜 **Activity Log**: Track every action taken by the agents

### Optional Automations
- 📧 **Send emails** via SendGrid (OFF by default — human-in-the-loop)
- 🔔 **Push notifications** for hot leads via Pushover (optional)

---

## 🏗️ Architecture (How It Works)

**Orchestrator Agent (SDR Manager)** runs a structured pipeline:

1. **🔬 Research Agent** → company/lead context (enrichment tool)
2. **📊 Qualifier Agent** → score, tier, reasoning, buying signals, next action  
3. **✍️ Email Writers (3 styles)** → generate alternative drafts
4. **🏆 Picker Agent** → selects the best email for response probability
5. **📬 Follow-up Agent** → writes follow-up sequence email
6. **🛠️ Tools** → save CRM note, (optional) send email, (optional) send push notification

**8 Specialized Agents collaborate:**
1. 🔬 **Lead Research Analyst** — Researches company & lead context
2. 📊 **Lead Qualification Specialist** — Scores & classifies leads (Hot/Warm/Cold)
3. ✍️ **Professional Email Writer** — Formal outreach style
4. 🎨 **Engaging Email Writer** — Witty, creative style
5. ⚡ **Concise Email Writer** — Short, direct style
6. 🏆 **Email Selection Expert** — Picks the best email draft
7. 📬 **Follow-up Email Writer** — Creates follow-up sequences
8. 🎯 **SDR Manager** — Orchestrates the entire pipeline

This is not a chatbot — it's a practical, tool-using **agentic workflow**.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Groq (free tier supported)<br>- Default: `llama-3.3-70b-versatile`<br>- Fast tasks: `llama-3.1-8b-instant` |
| **Agent Framework** | OpenAI Agents SDK |
| **Backend** | Python 3.11+ |
| **CRM Storage** | SQLite |
| **Dashboard** | Gradio |
| **Email** | SendGrid API (optional) |
| **Notifications** | Pushover API (optional) |

---

## 🚀 Quick Start

### 1) Clone & Install
```bash
git clone https://github.com/YOUR_USERNAME/ai-sdr-agent.git
cd ai-sdr-agent
pip install -r requirements.txt
2) Configure Environment (DO NOT commit secrets)
cp .env.example .env
# Edit .env locally with your keys
cp .env.example .env
Required:

GROQ_API_KEY — Get free at console.groq.com
Optional:

SENDGRID_API_KEY + SENDER_EMAIL (for sending emails)
PUSHOVER_USER + PUSHOVER_TOKEN (for notifications)
3) Run the Pipeline (Safe Mode — No Email Sending
# Process 3 sample leads
python -m src.run_pipeline --max-leads 3

# Process all leads
python -m src.run_pipeline

4) Launch the Dashboard
python dashboard/app.py

📁 CSV Format
Your CSV must include these columns:

csv

lead_id,first_name,last_name,email,job_title,company_name,company_size,industry,website,linkedin_url,lead_source,notes
A ready-to-run sample dataset is included:

data/sample_leads.csv (15 realistic SaaS leads)

⚖️ Ethical Use & Compliance Notes
This project is designed for ethical sales automation:

✅ Email sending is OFF by default (human-in-the-loop)
✅ Only references fields present in the lead record (no fake personalization)
✅ Avoids inferring protected characteristics (race, religion, politics, health, etc.)
✅ Recommended: Add opt-out language and comply with CAN-SPAM/GDPR applicable rules
If you deploy this for a real business, ensure your outreach practices follow applicable laws.

🗺️ Roadmap / Upgrade Options (Great for Client Work)
If you're hiring me (or using this repo as a base), I can extend it with:

HubSpot / Pipedrive / Salesforce integration
Google Sheets ingestion + continuous sync
Real enrichment (Clearbit/Apollo/LinkedIn-based sources where permitted)
Multi-step sequences (Day 1, Day 3, Day 7) + A/B testing
Approval queue in dashboard ("review → approve → send")
Team roles: SDR + manager review + audit logs
Deployment: Docker + Render/Fly.io + scheduled runs (cron)

💼 Want This Built For Your Business?
If you want this customized for your CRM, ICP, and outreach style, typical deliverables include:

ICP scoring tuned to your market
Email tone matching your brand voice
CRM integration + pipeline stages
Dashboard + reporting
Safe sending rules and compliance guardrails
Open an issue or contact me via Upwork with your CRM + lead source details.

📄 License
MIT License — Use freely for your projects.

<p align="center"> Built with ❤️ following the <strong>Ed Donner Agentic AI Course</strong> (Week 2, Day 2) pattern. </p> ```
To use this:

Create a folder docs/images/ in your repo
Take screenshots of your 6 dashboard tabs and save them as:
overview.png (stats cards view)
lead_detail.png (dropdown selector view)
run_pipeline.png (file upload view)
all_leads.png (table view)
activity_log.png (log table view)
about.png (architecture text view)
Or remove the image references if you don't want screenshots
Paste the above into README.md
Commit and push! 🚀
Open: http://localhost:7860
