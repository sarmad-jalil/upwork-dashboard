// Field names below match the Apify actor's real dataset output, verified
// against live scraper results.

/** 5873054.22 -> "$5.87M", 28271.86 -> "$28.3k", 532.58 -> "$533" */
export function formatMoney(value) {
  if (value == null || Number.isNaN(Number(value))) return null
  const n = Number(value)
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}k`
  return `$${Math.round(n)}`
}

/** "2026-08-30T18:18:28.565Z" -> "Aug 30, 18:18" */
export function formatPosted(value) {
  if (!value) return null
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Budget summary: hourly jobs carry price_min/price_max, fixed-price carry price. */
export function formatBudget(job) {
  if (job.price_min != null && job.price_max != null) {
    return `$${job.price_min}–$${job.price_max}/hr`
  }
  if (job.price != null) return `$${job.price}`
  return null
}

/** Buckets the actor's 0-100 job_score for colour-coding. Half of all jobs sit
 *  under 37 and only ~9% reach 70, so the thresholds skew low on purpose. */
export function scoreTier(score) {
  if (score == null) return 'none'
  if (score >= 65) return 'high'
  if (score >= 45) return 'mid'
  return 'low'
}

/** "2026-08-31T06:00:00Z" -> "3h ago" / "just now" / "2d ago" */
export function timeAgo(value) {
  if (!value) return null
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return null
  const mins = Math.round((Date.now() - d.getTime()) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.round(hours / 24)}d ago`
}

export function buildJobEvaluateRequest(job, model) {
  const body = {
    job_title: job.title,
    job_description: job.description,
    model,
  }

  // buyer_score is the client's 0-5 star rating.
  if (job.buyer_score != null) body.client_rating = Number(job.buyer_score)
  if (job.client_location) body.client_country = String(job.client_location)
  if (job.hire_rate != null) body.hire_rate = Number(job.hire_rate)
  if (job.avg_hourly_rate != null) body.avg_hourly_rate_paid = Number(job.avg_hourly_rate)

  const spent = formatMoney(job.total_spent)
  if (spent) body.total_spent = spent

  // The actor does not expose a proposals/applicants count, so it is omitted.
  return body
}

export function buildProposalRequest(job, { niche, experience, model }) {
  const body = {
    job_title: job.title,
    job_description: job.description,
    freelancer_niche: niche,
    model,
  }
  if (experience) body.relevant_experience = experience

  // Application instructions — clients use these to filter copy-paste applicants,
  // so the proposal has to satisfy them before anything else.
  if (Array.isArray(job.questions) && job.questions.length) {
    body.screening_questions = job.questions.map(String).filter(Boolean)
  }
  if (job.ai_specific_requirements_before_applying) {
    body.application_requirements = String(job.ai_specific_requirements_before_applying)
  }
  if (job.ai_anti_bot_phrase) body.anti_bot_phrase = String(job.ai_anti_bot_phrase)

  // Client signals — pitch a relationship vs a low-risk first win.
  if (job.buyer_score != null) body.client_rating = Number(job.buyer_score)
  if (job.client_location) body.client_location = String(job.client_location)
  if (job.hire_rate != null) body.hire_rate = Number(job.hire_rate)
  if (job.avg_hourly_rate != null) body.avg_hourly_rate_paid = Number(job.avg_hourly_rate)
  if (job.open_jobs != null) body.open_jobs = Number(job.open_jobs)

  const spent = formatMoney(job.total_spent)
  if (spent) body.total_spent = spent

  return body
}
