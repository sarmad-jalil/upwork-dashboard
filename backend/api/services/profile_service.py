from api.core.parsing import parse_llm_json
from api.models.schemas import (
    ModelChoice,
    ProfileAnalyzeRequest,
    ProfileAnalyzeResponse,
    ProfileScores,
)
from api.services.document_loader import get_chapter
from api.services.llm_router import call_llm

SYSTEM_PROMPT = """You are an expert Upwork profile coach. You analyze freelancer profiles using the proven optimization framework below.

=== UPWORK PROFILE OPTIMIZATION GUIDE ===
{chapter_1}
=== END OF GUIDE ===

Your job: analyze the given profile title and bio strictly based on this guide.

Respond ONLY with valid JSON in this exact structure:
{{
  "scores": {{
    "title_clarity": <0-10>,
    "bio_hook": <0-10>,
    "positioning": <0-10>,
    "simplicity": <0-10>,
    "overall": <0-10>
  }},
  "issues": ["issue 1", "issue 2", ...],
  "improvements": ["specific action 1", "specific action 2", ...],
  "suggested_title": "<rewritten title following guide rules>",
  "suggested_bio_opening": "<rewritten first 2 lines of bio following guide rules>"
}}

Scoring guide:
- title_clarity: Does title instantly show what they do + who they serve? (10 = perfect niche focus)
- bio_hook: Do first 2 lines state what/who/result without intro fluff? (10 = hooks immediately)
- positioning: Is profile focused on one type of client or scattered? (10 = laser focused)
- simplicity: Is language plain and clear, no buzzwords? (10 = simple and trustworthy)
- overall: Average of above scores

Be specific in issues and improvements. Reference exact phrases from their profile."""


def analyze_profile(req: ProfileAnalyzeRequest, api_key: str | None = None) -> ProfileAnalyzeResponse:
    chapter_1 = get_chapter("chapter_1")
    system = SYSTEM_PROMPT.format(chapter_1=chapter_1)

    user_message = f"""Please analyze this Upwork profile:

TITLE: {req.title}

BIO/OVERVIEW:
{req.bio}"""

    response = call_llm(provider=req.model, system=system, user=user_message, api_key=api_key)

    data = parse_llm_json(response.result)

    return ProfileAnalyzeResponse(
        scores=ProfileScores(**data["scores"]),
        issues=data["issues"],
        improvements=data["improvements"],
        suggested_title=data["suggested_title"],
        suggested_bio_opening=data["suggested_bio_opening"],
        model_used=response.model_used,
        provider=response.provider,
    )
