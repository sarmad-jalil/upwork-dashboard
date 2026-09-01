from api.core.parsing import parse_llm_json
from api.models.schemas import (
    TitleGenerateRequest,
    TitleGenerateResponse,
    TitleOption,
)
from api.services.document_loader import get_chapter
from api.services.llm_router import call_llm

SYSTEM_PROMPT = """You are an Upwork profile title expert. You write titles that get clients to instantly feel: "This person is exactly what I need."

=== UPWORK TITLE OPTIMIZATION GUIDE ===
{chapter_1}
=== END OF GUIDE ===

Generate 5 optimized profile titles strictly following these guide rules:
- Title must be CLEAR, not clever
- Must show the SPECIFIC SERVICE + TARGET CLIENT (not generic)
- No buzzwords: "expert", "guru", "ninja", "passionate", "dedicated"
- Pattern: "[Service] for [Target Client]" or "[Result] for [Target Client]"
- Short enough to read in 2 seconds

Respond ONLY with valid JSON in this exact structure:
{{
  "titles": [
    {{"title": "<title 1>", "why": "<one sentence why this works based on guide rules>"}},
    {{"title": "<title 2>", "why": "<why>"}},
    {{"title": "<title 3>", "why": "<why>"}},
    {{"title": "<title 4>", "why": "<why>"}},
    {{"title": "<title 5>", "why": "<why>"}}
  ],
  "best_pick": "<the single strongest title from the 5>"
}}"""


def generate_titles(req: TitleGenerateRequest, api_key: str | None = None) -> TitleGenerateResponse:
    chapter_1 = get_chapter("chapter_1")
    system = SYSTEM_PROMPT.format(chapter_1=chapter_1)

    current_title_block = (
        f"\nCURRENT TITLE (for reference/comparison): {req.current_title}"
        if req.current_title
        else ""
    )

    user_message = f"""Generate 5 optimized Upwork titles for this freelancer:

SKILLS: {req.skills}
TARGET CLIENTS: {req.target_clients}{current_title_block}"""

    response = call_llm(provider=req.model, system=system, user=user_message, api_key=api_key)

    data = parse_llm_json(response.result)

    return TitleGenerateResponse(
        titles=[TitleOption(**t) for t in data["titles"]],
        best_pick=data["best_pick"],
        model_used=response.model_used,
        provider=response.provider,
    )
