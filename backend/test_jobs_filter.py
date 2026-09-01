"""Regression tests for profile-driven job filtering.

No network, no keys, no pytest — run with:  python test_jobs_filter.py

Covers the bug where a profile's keywords were sent to the Apify actor as a
single `skills` string. The actor ANDs those terms, so any profile with 2+
keywords matched zero jobs. Keywords are now OR-matched locally instead.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from api.services.jobs_filter import expand_keywords, filter_relevant

results = []


def check(name, actual, expected):
    ok = actual == expected
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    if not ok:
        print(f"        expected: {expected}\n        actual:   {actual}")


def job(title, **over):
    base = {
        "id": title,
        "title": title,
        "description": "",
        "skills": "",
        "buyer_payment_verified": True,
        "client_location": "United States",
    }
    base.update(over)
    return base


PROFILE_KEYWORDS = [
    "MERN Stack", "MongoDB", "Express.js", "React.js", "Node.js",
    "JavaScript (ES6+)", "Redux / Redux Toolkit", "Git / GitHub", "Next.js",
]

# --- expand_keywords ------------------------------------------------------
check("splits on '/'", "redux toolkit" in expand_keywords(["Redux / Redux Toolkit"]), True)
check("keeps first alternative", "redux" in expand_keywords(["Redux / Redux Toolkit"]), True)
check("drops parenthetical", expand_keywords(["JavaScript (ES6+)"]), ["javascript"])
check("lowercases + keeps dots", expand_keywords(["Node.js"]), ["node.js"])
check("keeps multi-word phrase intact", expand_keywords(["MERN Stack"]), ["mern stack"])

# --- the regression: ANY keyword matches, not ALL -------------------------
one_match = [job("Need a React.js developer for a dashboard")]
check(
    "job matching ONE of many keywords is kept",
    len(filter_relevant(one_match, apply_stack_filters=False, match_keywords=PROFILE_KEYWORDS)),
    1,
)

many = [
    job("React.js developer needed"),
    job("MongoDB performance tuning"),
    job("Senior Python / Django engineer"),   # matches nothing in the profile
]
kept = filter_relevant(many, apply_stack_filters=False, match_keywords=PROFILE_KEYWORDS)
check("keeps only keyword matches", [j["title"] for j in kept],
      ["React.js developer needed", "MongoDB performance tuning"])

# --- no false positive from phrase splitting ------------------------------
check(
    "'MERN Stack' does not match a bare 'full stack' job",
    len(filter_relevant([job("Full stack engineer wanted")],
                        apply_stack_filters=False, match_keywords=["MERN Stack"])),
    0,
)

# --- matches against fields beyond the title ------------------------------
check(
    "matches on the skills field too",
    len(filter_relevant([job("Backend engineer", skills="Express.js, PostgreSQL")],
                        apply_stack_filters=False, match_keywords=PROFILE_KEYWORDS)),
    1,
)

# --- hard filters still apply on the profile path -------------------------
check(
    "unverified payment still dropped",
    len(filter_relevant([job("React.js role", buyer_payment_verified=False)],
                        apply_stack_filters=False, match_keywords=PROFILE_KEYWORDS)),
    0,
)
check(
    "excluded country still dropped",
    len(filter_relevant([job("React.js role", client_location="Israel")],
                        apply_stack_filters=False, match_keywords=PROFILE_KEYWORDS)),
    0,
)

# --- profile exclusions enforced locally ----------------------------------
# The actor's own exclude_keywords filter lets some through, so these must be
# dropped here regardless of what the scrape returned.
check(
    "excluded keyword drops the job (title)",
    len(filter_relevant([job("WordPress Developer Needed")],
                        apply_stack_filters=False, match_keywords=["React.js", "Node.js"],
                        exclude_keywords=["wordpress"])),
    0,
)
check(
    "exclusion beats a keyword match",
    len(filter_relevant([job("React.js dev to fix a WordPress theme")],
                        apply_stack_filters=False, match_keywords=["React.js"],
                        exclude_keywords=["wordpress"])),
    0,
)
check(
    "exclusion checks description/skills too",
    len(filter_relevant([job("Web developer", description="Built on Elementor")],
                        apply_stack_filters=False, match_keywords=["Web"],
                        exclude_keywords=["Elementor"])),
    0,
)
check(
    "unrelated job survives the exclusion",
    len(filter_relevant([job("React.js dashboard build")],
                        apply_stack_filters=False, match_keywords=["React.js"],
                        exclude_keywords=["wordpress"])),
    1,
)

# --- legacy no-profile path unchanged -------------------------------------
check(
    "legacy stack filter still keeps a React job",
    len(filter_relevant([job("React developer needed")], apply_stack_filters=True)),
    1,
)
check(
    "legacy stack filter still drops an off-stack job",
    len(filter_relevant([job("Bookkeeping and data entry")], apply_stack_filters=True)),
    0,
)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
