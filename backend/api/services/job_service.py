from api.core.parsing import parse_llm_json
from api.models.schemas import (
    ModelChoice,
    JobEvaluateRequest,
    JobEvaluateResponse,
)
from api.services.document_loader import get_chapters
from api.services.llm_router import call_llm

SYSTEM_PROMPT = """You are an expert Upwork job evaluator. You help freelancers decide whether a job is worth applying to, using the proven framework below.

=== UPWORK JOB SELECTION GUIDE ===
{chapters}
=== END OF GUIDE ===

Evaluate the job post and client details strictly based on this guide.

Respond ONLY with valid JSON in this exact structure:
{{
  "recommendation": "apply" or "skip",
  "score": <0-10>,
  "green_flags": ["positive signal 1", "positive signal 2", ...],
  "red_flags": ["warning 1", "warning 2", ...],
  "reason": "<2-3 sentence summary of why apply or skip>",
  "proposal_tips": ["specific tip 1 if applying", "tip 2", ...]
}}

Scoring guide (score out of 10):
- Client rating >= 4.5 = good (+2)
- Hire rate >= 50% = good (+2)
- Avg hourly rate paid >= $15 = good (+1), >= $30 = great (+2)
- Clear, specific job description = good (+1)
- Verified payment method mentioned = good (+1)
- Client from high-value country (US, UK, AU, CA, EU) = good (+1)
- Too many proposals already (50+) = warning (-1)
- Vague or unrealistic job post = warning (-1 to -2)
- No client history / new account = warning (-1)

recommendation: "apply" if score >= 6, else "skip"
proposal_tips: give 2-3 specific things to highlight based on what this client cares about.
If recommendation is "skip", proposal_tips should explain what to look for instead."""


def evaluate_job(req: JobEvaluateRequest, api_key: str | None = None) -> JobEvaluateResponse:
    chapters = get_chapters("chapter_2", "chapter_3")
    system = SYSTEM_PROMPT.format(chapters=chapters)

    client_info_lines = []
    if req.client_rating is not None:
        client_info_lines.append(f"Client Rating: {req.client_rating}/5")
    if req.client_country:
        client_info_lines.append(f"Client Country: {req.client_country}")
    if req.hire_rate is not None:
        client_info_lines.append(f"Hire Rate: {req.hire_rate}%")
    if req.avg_hourly_rate_paid is not None:
        client_info_lines.append(f"Avg Hourly Rate Paid: ${req.avg_hourly_rate_paid}")
    if req.total_spent:
        client_info_lines.append(f"Total Spent: {req.total_spent}")
    if req.proposals_count is not None:
        client_info_lines.append(f"Proposals Already Sent: {req.proposals_count}")

    client_info = "\n".join(client_info_lines) if client_info_lines else "No client stats provided"

    user_message = f"""Please evaluate this job post:

JOB TITLE: {req.job_title}

JOB DESCRIPTION:
{req.job_description}

CLIENT STATS:
{client_info}"""

    response = call_llm(provider=req.model, system=system, user=user_message, api_key=api_key)

    data = parse_llm_json(response.result)

    tips = data["proposal_tips"]
    if isinstance(tips, str):
        tips = [t.strip() for t in tips.split(".") if t.strip()]

    flags_green = data.get("green_flags", [])
    flags_red = data.get("red_flags", [])
    if isinstance(flags_green, str):
        flags_green = [flags_green]
    if isinstance(flags_red, str):
        flags_red = [flags_red]

    return JobEvaluateResponse(
        recommendation=data["recommendation"],
        score=data["score"],
        green_flags=flags_green,
        red_flags=flags_red,
        reason=data["reason"],
        proposal_tips=tips,
        model_used=response.model_used,
        provider=response.provider,
    )
