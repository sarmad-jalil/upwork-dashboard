import sys
sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings

client = TestClient(app)
settings = get_settings()

PASS = "PASS"
FAIL = "FAIL"
results = []


def check(name, response, expected_status=200, required_keys=None, check_fn=None):
    status = response.status_code
    try:
        body = response.json()
    except Exception:
        body = {}
    ok = status == expected_status
    if required_keys and ok:
        ok = all(k in body for k in required_keys)
    if check_fn and ok:
        ok = check_fn(body)
    tag = PASS if ok else FAIL
    results.append((tag, name))
    print(f"[{tag}] {name} — HTTP {status}")
    if not ok:
        print(f"       Body: {str(body)[:300]}")
    return body


def with_key(key):
    return {"X-API-Key": key}


print("=" * 50)
print("SECTION 1: Core Routes")
print("=" * 50)

check("GET /health", client.get("/health"), required_keys=["status"],
      check_fn=lambda b: b["status"] == "ok")

check("GET /", client.get("/"), required_keys=["message", "version"])


print()
print("=" * 50)
print("SECTION 2: Profile Analyzer")
print("=" * 50)

# Normal — uses .env key (fallback)
check(
    "Profile: valid request (env key fallback)",
    client.post("/profile/analyze", json={
        "title": "Creative Digital Expert Helping Brands Grow",
        "bio": "Hi I am a passionate freelancer with 5 years of experience in design, development, branding, logos and much more.",
        "model": "groq"
    }),
    required_keys=["scores", "issues", "improvements", "suggested_title", "suggested_bio_opening", "model_used", "provider"],
    check_fn=lambda b: 0 <= b["scores"]["overall"] <= 10
)

# BYOK — pass key explicitly via header
check(
    "Profile: valid request (X-API-Key header)",
    client.post("/profile/analyze",
        json={"title": "Python Developer for SaaS Startups", "bio": "I build REST APIs for SaaS companies using FastAPI and PostgreSQL.", "model": "groq"},
        headers=with_key(settings.groq_api_key)
    ),
    required_keys=["scores", "suggested_title"]
)

# Wrong model value → 422
check(
    "Profile: invalid model → 422",
    client.post("/profile/analyze", json={"title": "Dev", "bio": "I code.", "model": "gpt4"}),
    expected_status=422
)

# Missing title → 422
check(
    "Profile: missing title → 422",
    client.post("/profile/analyze", json={"bio": "I build things.", "model": "groq"}),
    expected_status=422
)

# Missing bio → 422
check(
    "Profile: missing bio → 422",
    client.post("/profile/analyze", json={"title": "Developer", "model": "groq"}),
    expected_status=422
)

# Bad key → 400
check(
    "Profile: invalid API key → 400 or 500",
    client.post("/profile/analyze",
        json={"title": "Developer", "bio": "I code.", "model": "groq"},
        headers=with_key("gsk_INVALID_KEY_12345")
    ),
    expected_status=None  # will check manually
)
# override: just check it's not 200
last = results.pop()
r = client.post("/profile/analyze",
    json={"title": "Developer", "bio": "I code.", "model": "groq"},
    headers=with_key("gsk_INVALID_KEY_12345")
)
tag = PASS if r.status_code != 200 else FAIL
results.append((tag, "Profile: invalid API key → non-200"))
print(f"[{tag}] Profile: invalid API key → non-200 — HTTP {r.status_code}")


print()
print("=" * 50)
print("SECTION 3: Job Evaluator")
print("=" * 50)

GOOD_JOB = {
    "job_title": "Shopify Store Redesign for DTC Brand",
    "job_description": "We run a DTC skincare brand. Need full Shopify redesign focused on conversion. Serious client, clear brief.",
    "client_rating": 4.9,
    "client_country": "United States",
    "hire_rate": 78.0,
    "avg_hourly_rate_paid": 45.0,
    "total_spent": "$50k+",
    "proposals_count": 8,
    "model": "groq"
}

BAD_JOB = {
    "job_title": "Need everything done ASAP and cheap",
    "job_description": "I need website logo social media SEO. Budget $50. Done by tomorrow.",
    "client_rating": 2.5,
    "hire_rate": 10.0,
    "proposals_count": 80,
    "model": "groq"
}

check(
    "Job: good job → apply",
    client.post("/job/evaluate", json=GOOD_JOB),
    required_keys=["recommendation", "score", "green_flags", "red_flags", "reason", "proposal_tips"],
    check_fn=lambda b: b["recommendation"] == "apply" and b["score"] >= 6
)

check(
    "Job: bad job → skip",
    client.post("/job/evaluate", json=BAD_JOB),
    required_keys=["recommendation", "score"],
    check_fn=lambda b: b["recommendation"] == "skip" and b["score"] <= 5
)

check(
    "Job: no client stats (minimal input)",
    client.post("/job/evaluate", json={
        "job_title": "FastAPI Developer needed",
        "job_description": "Need Python FastAPI developer for REST API project.",
        "model": "groq"
    }),
    required_keys=["recommendation", "score", "proposal_tips"]
)

check(
    "Job: with X-API-Key header",
    client.post("/job/evaluate", json=GOOD_JOB, headers=with_key(settings.groq_api_key)),
    required_keys=["recommendation", "score"]
)

check(
    "Job: missing job_title → 422",
    client.post("/job/evaluate", json={"job_description": "Need a dev.", "model": "groq"}),
    expected_status=422
)

check(
    "Job: client_rating out of range → 422",
    client.post("/job/evaluate", json={"job_title": "Dev", "job_description": "Need dev.", "client_rating": 9.0, "model": "groq"}),
    expected_status=422
)


print()
print("=" * 50)
print("SECTION 4: Proposal Generator")
print("=" * 50)

PROPOSAL_BASE = {
    "job_title": "B2B SaaS Landing Page Design",
    "job_description": "Need high-converting landing page for SaaS product. Traffic coming but not converting.",
    "freelancer_niche": "Landing page designer for B2B SaaS companies",
    "model": "groq"
}

check(
    "Proposal: basic generation",
    client.post("/proposal/generate", json=PROPOSAL_BASE),
    required_keys=["proposal", "opening_question", "micro_win", "word_count", "model_used"],
    check_fn=lambda b: 50 <= b["word_count"] <= 300
)

check(
    "Proposal: with relevant experience",
    client.post("/proposal/generate", json={**PROPOSAL_BASE, "relevant_experience": "Built 5 SaaS landing pages, avg 40% conversion lift."}),
    required_keys=["proposal", "word_count"]
)

check(
    "Proposal: with X-API-Key header",
    client.post("/proposal/generate", json=PROPOSAL_BASE, headers=with_key(settings.groq_api_key)),
    required_keys=["proposal", "opening_question"]
)

check(
    "Proposal: missing niche → 422",
    client.post("/proposal/generate", json={"job_title": "Dev job", "job_description": "Need dev.", "model": "groq"}),
    expected_status=422
)

check(
    "Proposal: mistral model",
    client.post("/proposal/generate", json={**PROPOSAL_BASE, "model": "mistral"}),
    required_keys=["proposal", "word_count"],
    check_fn=lambda b: b["word_count"] > 0
)


print()
print("=" * 50)
print("SECTION 5: Title Generator")
print("=" * 50)

TITLES_BASE = {
    "skills": "Python, FastAPI, PostgreSQL, REST APIs",
    "target_clients": "SaaS startups and tech companies",
    "model": "groq"
}

check(
    "Titles: basic generation",
    client.post("/tools/generate-titles", json=TITLES_BASE),
    required_keys=["titles", "best_pick", "model_used"],
    check_fn=lambda b: len(b["titles"]) == 5 and b["best_pick"]
)

check(
    "Titles: with current title",
    client.post("/tools/generate-titles", json={**TITLES_BASE, "current_title": "Python Expert"}),
    required_keys=["titles", "best_pick"],
    check_fn=lambda b: len(b["titles"]) == 5
)

check(
    "Titles: with X-API-Key header",
    client.post("/tools/generate-titles", json=TITLES_BASE, headers=with_key(settings.groq_api_key)),
    required_keys=["titles", "best_pick"]
)

check(
    "Titles: mistral model",
    client.post("/tools/generate-titles", json={**TITLES_BASE, "model": "mistral"}),
    required_keys=["titles", "best_pick"]
)

check(
    "Titles: missing skills → 422",
    client.post("/tools/generate-titles", json={"target_clients": "SaaS", "model": "groq"}),
    expected_status=422
)


print()
print("=" * 50)
print("SECTION 6: Conversion Coach")
print("=" * 50)

check(
    "Coach: basic reply",
    client.post("/tools/conversion-coach", json={
        "client_message": "Looks interesting. What is your rate and how long would this take?",
        "context": "Client posted Shopify redesign job. I sent proposal yesterday.",
        "model": "groq"
    }),
    required_keys=["suggested_reply", "tactic_used", "what_to_avoid", "model_used"]
)

check(
    "Coach: no context (optional field)",
    client.post("/tools/conversion-coach", json={
        "client_message": "Can you share some examples of your work?",
        "model": "groq"
    }),
    required_keys=["suggested_reply", "tactic_used", "what_to_avoid"]
)

check(
    "Coach: follow-up silence message",
    client.post("/tools/conversion-coach", json={
        "client_message": "Hey just checking in, any update?",
        "model": "mistral"
    }),
    required_keys=["suggested_reply"]
)

check(
    "Coach: with X-API-Key header",
    client.post("/tools/conversion-coach", json={
        "client_message": "What would be the first step if we work together?",
        "model": "groq"
    }, headers=with_key(settings.groq_api_key)),
    required_keys=["suggested_reply", "tactic_used"]
)

check(
    "Coach: missing client_message → 422",
    client.post("/tools/conversion-coach", json={"model": "groq"}),
    expected_status=422
)


print()
print("=" * 50)
print("SECTION 7: BYOK — key priority logic")
print("=" * 50)

# Header key takes priority — verify provider echoed back correctly
r = client.post("/profile/analyze",
    json={"title": "Dev", "bio": "I build APIs for startups.", "model": "groq"},
    headers=with_key(settings.groq_api_key)
)
tag = PASS if r.status_code == 200 and r.json().get("provider") == "groq" else FAIL
results.append((tag, "BYOK: header key used, provider=groq confirmed"))
print(f"[{tag}] BYOK: header key used, provider=groq confirmed — HTTP {r.status_code}")

# No key in header, no .env → 400
from unittest.mock import patch
from app.core.config import Settings
empty_settings = Settings(groq_api_key="", mistral_api_key="", anthropic_api_key="")
with patch("app.services.llm_router.get_settings", return_value=empty_settings):
    r2 = client.post("/profile/analyze",
        json={"title": "Dev", "bio": "I build things.", "model": "groq"}
    )
tag2 = PASS if r2.status_code in (400, 500) else FAIL
results.append((tag2, "BYOK: no key anywhere → 400/500"))
print(f"[{tag2}] BYOK: no key anywhere → 400/500 — HTTP {r2.status_code}")


print()
print("=" * 50)
passed = sum(1 for t, _ in results if t == PASS)
failed = sum(1 for t, _ in results if t == FAIL)
total = len(results)
print(f"RESULTS: {passed} passed / {failed} failed / {total} total")
if failed:
    print()
    print("FAILED:")
    for tag, name in results:
        if tag == FAIL:
            print(f"  ✗ {name}")
else:
    print("All tests passed.")
