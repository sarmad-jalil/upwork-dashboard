from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field, BeforeValidator

CoercedInt = Annotated[int, BeforeValidator(lambda v: int(round(float(v))))]


class ModelChoice(str, Enum):
    claude = "claude"
    mistral = "mistral"
    groq = "groq"


class LLMResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_used: str
    provider: ModelChoice
    result: str


# --- Profile Analyzer ---

class ProfileAnalyzeRequest(BaseModel):
    title: str = Field(..., description="Your current Upwork profile title")
    bio: str = Field(..., description="Your profile overview/bio text")
    model: ModelChoice = Field(ModelChoice.groq, description="LLM provider to use")


class ProfileScores(BaseModel):
    title_clarity: CoercedInt = Field(..., ge=0, le=10)
    bio_hook: CoercedInt = Field(..., ge=0, le=10)
    positioning: CoercedInt = Field(..., ge=0, le=10)
    simplicity: CoercedInt = Field(..., ge=0, le=10)
    overall: CoercedInt = Field(..., ge=0, le=10)


class ProfileAnalyzeResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    scores: ProfileScores
    issues: list[str]
    improvements: list[str]
    suggested_title: str
    suggested_bio_opening: str
    model_used: str
    provider: ModelChoice


# --- Job Evaluator ---

class JobEvaluateRequest(BaseModel):
    job_title: str = Field(..., description="Title of the job post")
    job_description: str = Field(..., description="Full job description text")
    client_rating: float | None = Field(None, ge=0, le=5, description="Client rating (0-5)")
    client_country: str | None = Field(None, description="Client's country")
    hire_rate: float | None = Field(None, ge=0, le=100, description="Client hire rate percentage")
    avg_hourly_rate_paid: float | None = Field(None, description="Average hourly rate client has paid")
    total_spent: str | None = Field(None, description="Total amount client has spent on Upwork e.g. '$10k+'")
    proposals_count: int | None = Field(None, description="Number of proposals already sent")
    model: ModelChoice = Field(ModelChoice.groq, description="LLM provider to use")


class JobEvaluateResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    recommendation: str = Field(..., description="'apply' or 'skip'")
    score: int = Field(..., ge=0, le=10, description="Job quality score")
    green_flags: list[str]
    red_flags: list[str]
    reason: str = Field(..., description="Short summary of the recommendation")
    proposal_tips: list[str] = Field(..., description="What to emphasize if you apply")
    model_used: str
    provider: ModelChoice


# --- Proposal Generator ---

class ProposalGenerateRequest(BaseModel):
    job_title: str = Field(..., description="Title of the job post")
    job_description: str = Field(..., description="Full job description text")
    freelancer_niche: str = Field(..., description="Your niche/positioning e.g. 'Shopify store designer for DTC brands'")
    relevant_experience: str | None = Field(None, description="Specific experience or past work to reference")
    model: ModelChoice = Field(ModelChoice.groq, description="LLM provider to use")

    # Application instructions — clients use these to filter copy-paste
    # applicants, so they must be obeyed before anything else is written.
    screening_questions: list[str] = Field(default_factory=list)
    application_requirements: str | None = Field(None, description="Stated requirements to satisfy before applying")
    anti_bot_phrase: str | None = Field(None, description="Phrase/word the client asks applicants to include")

    # Client signals — shape whether to pitch a relationship or a low-risk first win.
    client_rating: float | None = Field(None, ge=0, le=5)
    client_location: str | None = None
    hire_rate: float | None = Field(None, ge=0, le=100)
    total_spent: str | None = None
    avg_hourly_rate_paid: float | None = None
    open_jobs: int | None = Field(None, description="Client's currently open jobs — parallel hiring signal")


class ProposalGenerateResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    proposal: str = Field(..., description="Full ready-to-send proposal text")
    opening_question: str = Field(..., description="The hook question used to open")
    micro_win: str = Field(..., description="The small suggestion/insight given to the client")
    word_count: int
    model_used: str
    provider: ModelChoice


# --- Title Generator ---

class TitleGenerateRequest(BaseModel):
    skills: str = Field(..., description="Your main skills e.g. 'Shopify, e-commerce, conversion design'")
    target_clients: str = Field(..., description="Who you want to work with e.g. 'DTC brands, Shopify stores'")
    current_title: str | None = Field(None, description="Your current title (optional, for comparison)")
    model: ModelChoice = Field(ModelChoice.groq, description="LLM provider to use")


class TitleOption(BaseModel):
    title: str
    why: str = Field(..., description="Why this title works based on the guide")


class TitleGenerateResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    titles: list[TitleOption]
    best_pick: str = Field(..., description="The single strongest title recommendation")
    model_used: str
    provider: ModelChoice


# --- Conversion Coach ---

class ConversionCoachRequest(BaseModel):
    client_message: str = Field(..., description="The message the client sent you")
    context: str | None = Field(None, description="Any context about the job or prior conversation")
    model: ModelChoice = Field(ModelChoice.groq, description="LLM provider to use")


class ConversionCoachResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    suggested_reply: str = Field(..., description="Ready-to-send reply to the client")
    tactic_used: str = Field(..., description="Which Chapter 6 tactic was applied and why")
    what_to_avoid: str = Field(..., description="What NOT to say in this situation")
    model_used: str
    provider: ModelChoice


# --- Jobs Scraper ---

class JobListing(BaseModel):
    """One job from the Apify actor.

    Field names/types mirror the actor's real dataset output. `extra="allow"`
    keeps any field the actor adds later, and every field is optional because
    the actor omits most of them depending on job type (hourly vs fixed-price).
    """

    model_config = {"extra": "allow"}

    id: str | None = None
    url: str | None = None
    title: str | None = None
    description: str | None = None
    skills: str | None = None
    date_posted: str | None = None
    created_at: str | None = None

    # Pricing — fixed-price jobs use `price`, hourly jobs use price_min/price_max.
    price_type: str | None = None
    price: float | None = None
    price_min: float | None = None
    price_max: float | None = None

    # Client / buyer stats
    client_location: str | None = None
    buyer_city: str | None = None
    buyer_payment_verified: bool | None = None
    buyer_score: float | None = None
    buyer_feedback_count: int | None = None
    total_spent: float | None = None
    avg_hourly_rate: float | None = None
    hire_rate: float | None = None
    hires: int | None = None
    jobs_posted: int | None = None
    open_jobs: int | None = None
    total_hours: int | None = None

    # Categorisation / scoring
    job_score: float | None = None
    category_name: str | None = None
    subcategory_name: str | None = None
    experience_level: str | None = None
    questions: list | None = None

    # AI-derived fields from the actor
    ai_technical_skills: str | None = None
    ai_inferred_technical_skills: str | None = None
    ai_specific_requirements_before_applying: str | None = None
    ai_anti_bot_phrase: str | None = None


# --- Profiles ---

class ProfileCreateRequest(BaseModel):
    name: str = Field(..., description="Label for this profile e.g. 'Shopify DTC'")
    niche: str = Field(..., description="Your positioning/niche, used to search for jobs e.g. 'Shopify store designer for DTC brands'")
    keywords: list[str] = Field(default_factory=list, description="Skills a job should match e.g. ['Shopify', 'e-commerce']")
    exclude_keywords: list[str] = Field(default_factory=list, description="Jobs containing any of these are dropped")
    experience: str | None = Field(None, description="Relevant experience, used for proposal generation")
    model: ModelChoice = Field(ModelChoice.groq, description="LLM provider used for Evaluate & Generate Proposal")
    min_job_score: int = Field(40, ge=0, le=100, description="Minimum Apify job_score (0-100) to include when scraping")


class ProfileUpdateRequest(BaseModel):
    """Partial update — only the fields actually sent are written.

    `is_active` is deliberately absent: switching the active profile goes
    through POST /profiles/{id}/activate so exactly one stays active.
    """

    name: str | None = None
    niche: str | None = None
    keywords: list[str] | None = None
    exclude_keywords: list[str] | None = None
    experience: str | None = None
    model: ModelChoice | None = None
    min_job_score: int | None = Field(None, ge=0, le=100)


class ProfileResponse(BaseModel):
    id: int
    name: str
    niche: str
    keywords: list[str]
    exclude_keywords: list[str]
    experience: str | None
    model: ModelChoice
    min_job_score: int
    is_active: bool
    created_at: str


class ProfileListResponse(BaseModel):
    profiles: list[ProfileResponse]


class JobsScrapeResponse(BaseModel):
    jobs: list[JobListing]
    total_scraped: int
    new_count: int = Field(0, description="Jobs new to this profile in this run")
    pages_scanned: int = Field(1, description="Actor calls made (time windows walked)")
    total_after_filter: int
