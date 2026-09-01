import re
import json


def parse_llm_json(raw: str) -> dict:
    # Strip markdown code fences
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    # Remove trailing commas before ] or } (common model mistake)
    text = re.sub(r",\s*([}\]])", r"\1", text)

    return json.loads(text)
