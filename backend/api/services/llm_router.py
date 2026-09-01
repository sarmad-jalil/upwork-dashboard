from api.core.config import get_settings
from api.models.schemas import ModelChoice, LLMResponse

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
MISTRAL_MODEL = "mistral-small-latest"
GROQ_MODEL = "openai/gpt-oss-120b"


def _resolve_key(user_key: str | None, env_key: str, placeholder: str, label: str) -> str:
    key = user_key or env_key
    if not key or key == placeholder:
        raise ValueError(
            f"{label} API key not provided. Pass it via X-API-Key header or configure in .env"
        )
    return key


def _call_claude(system: str, user: str, api_key: str | None = None) -> str:
    import anthropic

    settings = get_settings()
    key = _resolve_key(api_key, settings.anthropic_api_key, "your_anthropic_key_here", "Anthropic")
    client = anthropic.Anthropic(api_key=key)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


def _call_mistral(system: str, user: str, api_key: str | None = None) -> str:
    from mistralai import Mistral

    settings = get_settings()
    key = _resolve_key(api_key, settings.mistral_api_key, "your_mistral_key_here", "Mistral")
    client = Mistral(api_key=key)
    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def _call_groq(system: str, user: str, api_key: str | None = None) -> str:
    from groq import Groq

    settings = get_settings()
    key = _resolve_key(api_key, settings.groq_api_key, "your_groq_key_here", "Groq")
    client = Groq(api_key=key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=2048,
    )
    return response.choices[0].message.content


def call_llm(
    provider: ModelChoice,
    system: str,
    user: str,
    api_key: str | None = None,
) -> LLMResponse:
    if provider == ModelChoice.claude:
        text = _call_claude(system, user, api_key)
        model_used = CLAUDE_MODEL
    elif provider == ModelChoice.mistral:
        text = _call_mistral(system, user, api_key)
        model_used = MISTRAL_MODEL
    elif provider == ModelChoice.groq:
        text = _call_groq(system, user, api_key)
        model_used = GROQ_MODEL
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return LLMResponse(model_used=model_used, provider=provider, result=text)
