import os


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


SCRAPER_ACTOR = os.getenv("JOBS_SCRAPER_ACTOR", "hyperbach/upwork-scraper-ai")

DEFAULT_SCRAPE_INPUT = {
    "category_name": os.getenv("JOBS_CATEGORY_NAME", "Web, Mobile & Software Dev"),
    "date_posted": os.getenv("JOBS_DATE_POSTED", "1d"),
    "buyer_payment_verified": True,
    "exclude_keywords": os.getenv("JOBS_EXCLUDE_KEYWORDS", "Israel"),
    "job_score": os.getenv("JOBS_MIN_SCORE", ">=40"),
    "limit": int(os.getenv("JOBS_DEFAULT_LIMIT", "50")),
}

STACK_KEYWORDS = _split_csv(os.getenv("JOBS_STACK_KEYWORDS", ",".join([
    "react", "next.js", "nextjs", "next js", "node", "express",
    "javascript", "typescript", "full-stack", "fullstack", "full stack",
    "front-end", "frontend", "front end", "mern", "tailwind",
    "mongodb", "postgres", "postgresql", "mysql", "supabase", "firebase",
    "rest api", "api integration", "jwt",
])))

EXCLUDE_ROLE_HINTS = _split_csv(os.getenv("JOBS_EXCLUDE_ROLE_HINTS", ",".join([
    "wix", "shopify", "squarespace", "webflow", "woocommerce", "odoo",
    "bricks builder", "qa tester", "tester in", "functional consultant",
])))

STRONG_DEV_KEYWORDS = [
    "react", "node.js", "nodejs", "node ", "next.js", "nextjs",
    "express", "full-stack", "fullstack", "full stack", "mern",
]

EXCLUDE_TITLE_TERMS = ["qa tester", "consultant"]

REQUIRE_PAYMENT_VERIFIED = os.getenv("JOBS_REQUIRE_PAYMENT_VERIFIED", "true").lower() == "true"
MAX_AGE_HOURS = int(os.getenv("JOBS_MAX_AGE_HOURS", "24"))
EXCLUDE_COUNTRIES = _split_csv(os.getenv("JOBS_EXCLUDE_COUNTRIES", "israel,isr"))

# One actor call returns at most `limit` jobs from a single stable slice, so a
# refresh walks the window backwards to reach the rest of the pool. Each page is
# billed, so these bound one refresh at MAX_PAGES * JOBS_DEFAULT_LIMIT jobs.
MAX_PAGES = int(os.getenv("JOBS_MAX_PAGES", "4"))
TARGET_NEW_JOBS = int(os.getenv("JOBS_TARGET_NEW", "25"))
