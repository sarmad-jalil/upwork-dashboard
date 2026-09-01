from api.core.parsing import parse_llm_json
from api.models.schemas import (
    ConversionCoachRequest,
    ConversionCoachResponse,
)
from api.services.document_loader import get_chapter
from api.services.llm_router import call_llm

SYSTEM_PROMPT = """You are an Upwork client conversion expert. You help freelancers reply to client messages in a way that moves conversations toward a hire — without being pushy or needy.

=== UPWORK CLIENT CONVERSION GUIDE ===
{chapter_6}
=== END OF GUIDE ===

Analyze the client's message and write the best possible reply using the guide's tactics.

Key tactics from the guide:
- First reply matters more than the proposal — be fast AND clear
- Lead the conversation, don't just answer and wait
- Don't rush into price — understand their need first
- Use the "Mini Plan" trick: briefly show HOW you'd do it
- Reduce their risk: suggest starting small or with milestones
- Close calmly: "Let me know if you'd like to start, I can begin with [X] right away"
- Never say "please hire me" or sound needy

Respond ONLY with valid JSON in this exact structure:
{{
  "suggested_reply": "<ready-to-send reply to the client>",
  "tactic_used": "<which guide tactic you applied and exactly why it fits this message>",
  "what_to_avoid": "<what most freelancers would say wrong here and why it fails>"
}}"""


def conversion_coach(req: ConversionCoachRequest, api_key: str | None = None) -> ConversionCoachResponse:
    chapter_6 = get_chapter("chapter_6")
    system = SYSTEM_PROMPT.format(chapter_6=chapter_6)

    context_block = (
        f"\nCONTEXT / PRIOR CONVERSATION:\n{req.context}"
        if req.context
        else ""
    )

    user_message = f"""How should I reply to this client message?

CLIENT MESSAGE:
{req.client_message}{context_block}"""

    response = call_llm(provider=req.model, system=system, user=user_message, api_key=api_key)

    data = parse_llm_json(response.result)

    return ConversionCoachResponse(
        suggested_reply=data["suggested_reply"],
        tactic_used=data["tactic_used"],
        what_to_avoid=data["what_to_avoid"],
        model_used=response.model_used,
        provider=response.provider,
    )
