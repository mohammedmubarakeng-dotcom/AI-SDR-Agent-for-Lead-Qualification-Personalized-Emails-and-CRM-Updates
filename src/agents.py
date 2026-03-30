"""
AI Agent definitions using OpenAI Agents SDK with Groq backend.
Following the Ed Donner lab notebook pattern — Agent workflow, tools, handoffs.
"""

import os
from agents import Agent, function_tool
from src.config import PRIMARY_MODEL, FAST_MODEL, ICP
from src.tools import send_outreach_email, send_pushover_notification, save_crm_note, lookup_company_info

# ============================================================
# Set Groq as the OpenAI-compatible backend
# ============================================================
os.environ["OPENAI_API_KEY"] = os.environ.get("GROQ_API_KEY", "")
os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"


# ============================================================
# ICP string for agent instructions
# ============================================================
ICP_STR = f"""
TARGET INDUSTRIES: {', '.join(ICP['target_industries'])}
TARGET TITLES: {', '.join(ICP['target_titles'])}
COMPANY SIZE: {ICP['company_size']['min']}-{ICP['company_size']['max']} employees (ideal: {ICP['company_size']['ideal_min']}-{ICP['company_size']['ideal_max']})
BUYING SIGNALS: {', '.join(ICP['signals'])}
OUR COMPANY: {ICP['company_description']}
"""


# ============================================================
# Agent 1: Lead Researcher
# ============================================================
researcher_instructions = f"""You are a Lead Research Analyst for ComplAI.

Your job is to analyze a lead and research their company. You will be given lead information.

Use the lookup_company_info tool to research the company.

Then provide a comprehensive research report including:
1. Company overview and what they do
2. Why they might need compliance/SOC2 tools
3. Key pain points you can identify
4. Buying signals detected
5. Any risks or red flags

Be thorough but concise. This research will be used by other agents to qualify the lead and write emails.

{ICP_STR}
"""

lead_researcher = Agent(
    name="Lead Research Analyst",
    instructions=researcher_instructions,
    tools=[lookup_company_info],
    model=PRIMARY_MODEL,
)


# ============================================================
# Agent 2: Lead Qualifier / Scorer
# ============================================================
qualifier_instructions = f"""You are a Lead Qualification Specialist for ComplAI.

You analyze lead information and research reports to score and qualify leads.

SCORING CRITERIA (0-100 points):
- Industry Match (0-25): Is the lead's industry in our target list?
- Title/Seniority Match (0-25): Is the person a decision maker?
- Company Size Match (0-20): Is the company in our ideal size range?
- Buying Signals (0-20): Are there signals they need our product?
- Lead Source Quality (0-10): Did they come inbound or from a referral?

TIER CLASSIFICATION:
- HOT (75-100): Strong ICP match, clear buying signals, decision maker
- WARM (45-74): Partial ICP match, some signals, worth pursuing
- COLD (0-44): Poor fit, wrong industry/size, no signals

You MUST respond in EXACTLY this format (use these exact labels):

SCORE: [number 0-100]
TIER: [hot/warm/cold]
REASONING: [2-3 sentences explaining the score]
ICP_MATCH: [specific ICP match details]
BUYING_SIGNALS: [detected buying signals or "None detected"]
NEXT_ACTION: [recommended next step]
CRM_NOTE: [brief note for CRM]

{ICP_STR}
"""

lead_qualifier = Agent(
    name="Lead Qualification Specialist",
    instructions=qualifier_instructions,
    model=PRIMARY_MODEL,
)


# ============================================================
# Agent 3: Professional Email Writer
# ============================================================
email_writer_professional = Agent(
    name="Professional Email Writer",
    instructions=f"""You are a professional sales email writer for ComplAI.
{ICP['company_description']}

Write formal, professional cold outreach emails that:
- Address the lead by first name
- Reference their specific company and role
- Mention a relevant pain point based on their industry
- Present ComplAI as the solution
- Include a clear, specific call to action
- Keep it under 150 words
- Sound human, not robotic

You MUST respond in EXACTLY this format:

SUBJECT: [email subject line]
---
BODY:
[email body text]
""",
    model=PRIMARY_MODEL,
)


# ============================================================
# Agent 4: Engaging/Witty Email Writer
# ============================================================
email_writer_engaging = Agent(
    name="Engaging Email Writer",
    instructions=f"""You are a witty, engaging sales email writer for ComplAI.
{ICP['company_description']}

Write creative, attention-grabbing cold outreach emails that:
- Use a hook or interesting opening line
- Show personality while remaining professional
- Reference the lead's specific situation
- Make compliance sound less boring
- Include light humor where appropriate
- End with a compelling CTA
- Keep it under 150 words

You MUST respond in EXACTLY this format:

SUBJECT: [email subject line]
---
BODY:
[email body text]
""",
    model=PRIMARY_MODEL,
)


# ============================================================
# Agent 5: Concise Email Writer
# ============================================================
email_writer_concise = Agent(
    name="Concise Email Writer",
    instructions=f"""You are a concise, direct sales email writer for ComplAI.
{ICP['company_description']}

Write short, impactful cold outreach emails that:
- Get straight to the point
- Lead with value, not features
- Use short paragraphs (1-2 sentences each)
- Reference one specific, relevant pain point
- Include a simple yes/no CTA
- Keep it under 80 words total

You MUST respond in EXACTLY this format:

SUBJECT: [email subject line]
---
BODY:
[email body text]
""",
    model=PRIMARY_MODEL,
)


# ============================================================
# Agent 6: Follow-up Email Writer
# ============================================================
follow_up_writer = Agent(
    name="Follow-up Email Writer",
    instructions=f"""You are a follow-up email specialist for ComplAI.
{ICP['company_description']}

Write a follow-up email (to send 3 days after the first email) that:
- References the previous email without being pushy
- Adds new value (a stat, case study reference, or insight)
- Is shorter than the first email
- Has a different angle/hook
- Includes a low-pressure CTA
- Keep it under 100 words

You MUST respond in EXACTLY this format:

SUBJECT: [follow-up subject line]
---
BODY:
[follow-up email body]
""",
    model=PRIMARY_MODEL,
)


# ============================================================
# Agent 7: Email Picker (selects best email)
# ============================================================
email_picker = Agent(
    name="Email Selection Expert",
    instructions="""You are an expert at evaluating cold sales emails.

You will be given multiple email drafts for the same lead.

Pick the SINGLE BEST email based on:
1. Personalization — does it reference the lead's specific situation?
2. Value proposition — does it clearly explain the benefit?
3. Call to action — is the CTA clear and compelling?
4. Length — is it concise enough to actually get read?
5. Subject line — would it get opened?

Respond with ONLY the selected email in this exact format:

SUBJECT: [the subject of the winning email]
---
BODY:
[the body of the winning email]

Do NOT add any explanation. Just output the winning email.
""",
    model=PRIMARY_MODEL,
)


# ============================================================
# Agent 8: HTML Converter
# ============================================================
html_converter = Agent(
    name="HTML Email Converter",
    instructions="""You convert a plain text email body into a clean, professional HTML email.

Use:
- Simple, inline CSS styles
- A clean, readable layout
- Professional font (Arial or Helvetica)
- Proper paragraph spacing
- A styled CTA button for any call to action link
- Responsive design principles

Keep it clean and modern. Do NOT use complex tables or images.
Return ONLY the HTML code, nothing else.
""",
    model=FAST_MODEL,
)


# ============================================================
# Convert agents to tools (following Ed Donner pattern)
# ============================================================
researcher_tool = lead_researcher.as_tool(
    tool_name="research_lead",
    tool_description="Research a lead and their company. Input the lead details as a string."
)

qualifier_tool = lead_qualifier.as_tool(
    tool_name="qualify_lead",
    tool_description="Qualify and score a lead based on ICP. Input the lead details and research as a string."
)

email_tool_professional = email_writer_professional.as_tool(
    tool_name="write_professional_email",
    tool_description="Write a professional cold outreach email for a lead."
)

email_tool_engaging = email_writer_engaging.as_tool(
    tool_name="write_engaging_email",
    tool_description="Write an engaging, witty cold outreach email for a lead."
)

email_tool_concise = email_writer_concise.as_tool(
    tool_name="write_concise_email",
    tool_description="Write a concise, direct cold outreach email for a lead."
)

email_picker_tool = email_picker.as_tool(
    tool_name="pick_best_email",
    tool_description="Pick the best email from multiple drafts. Input all email drafts."
)

follow_up_tool = follow_up_writer.as_tool(
    tool_name="write_follow_up_email",
    tool_description="Write a follow-up email for a lead."
)

html_converter_tool = html_converter.as_tool(
    tool_name="convert_to_html",
    tool_description="Convert a plain text email to HTML format."
)


# ============================================================
# SDR Manager Agent — the orchestrator (following Ed Donner pattern)
# ============================================================
sdr_manager_instructions = f"""
You are the SDR Manager at ComplAI. You orchestrate the entire lead qualification and outreach process.

{ICP['company_description']}

For EACH lead you receive, follow these steps IN ORDER:

STEP 1 - RESEARCH: Use the research_lead tool to research the lead and their company.

STEP 2 - QUALIFY: Use the qualify_lead tool with the lead info AND research results to get a qualification score.

STEP 3 - EMAILS (only if score >= 45, i.e., hot or warm):
  a) Use write_professional_email tool with lead info + research
  b) Use write_engaging_email tool with lead info + research
  c) Use write_concise_email tool with lead info + research
  d) Use pick_best_email tool to select the best email from all three drafts

STEP 4 - FOLLOW UP (only if score >= 45):
  Use write_follow_up_email tool for the lead

STEP 5 - CRM NOTE:
  Use save_crm_note tool to save a note about this lead with the qualification results

STEP 6 - FINAL REPORT:
  Provide a structured final report with ALL of the following clearly labeled:

  LEAD_ID: [id]
  LEAD_NAME: [full name]
  COMPANY: [company name]
  SCORE: [0-100]
  TIER: [hot/warm/cold]
  REASONING: [why this score]
  ICP_MATCH: [match details]
  BUYING_SIGNALS: [signals found]
  BEST_EMAIL_SUBJECT: [subject line of best email]
  BEST_EMAIL_BODY: [body of best email]
  FOLLOW_UP_SUBJECT: [follow-up subject line]
  FOLLOW_UP_BODY: [follow-up body]
  CRM_NOTE: [note saved]
  NEXT_ACTION: [recommended next step]

IMPORTANT RULES:
- Process the lead completely through all steps
- For cold leads (score < 45), skip email writing but still provide the report
- Always save a CRM note
- Be thorough in your research and qualification
"""

sdr_manager = Agent(
    name="SDR Manager",
    instructions=sdr_manager_instructions,
    tools=[
        researcher_tool,
        qualifier_tool,
        email_tool_professional,
        email_tool_engaging,
        email_tool_concise,
        email_picker_tool,
        follow_up_tool,
        save_crm_note,
    ],
    model=PRIMARY_MODEL,
)