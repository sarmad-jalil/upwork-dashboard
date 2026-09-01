import { useState } from 'react'
import JobCard from './JobCard'
import { scoreTier } from './jobMapping'

const SORTS = {
  score: { label: 'Best score', fn: (a, b) => (b.job_score ?? -1) - (a.job_score ?? -1) },
  newest: { label: 'Newest', fn: (a, b) => new Date(b.date_posted ?? 0) - new Date(a.date_posted ?? 0) },
}

export default function JobsList({ data, profile, source }) {
  const [sort, setSort] = useState('score')
  const [verifiedOnly, setVerifiedOnly] = useState(false)

  let jobs = [...data.jobs]
  if (verifiedOnly) jobs = jobs.filter((j) => j.buyer_payment_verified)
  jobs.sort(SORTS[sort].fn)

  const strong = data.jobs.filter((j) => scoreTier(j.job_score) === 'high').length

  return (
    <div className="result">
      <div className="jobs-toolbar">
        <div>
          <h3 style={{ marginBottom: 4 }}>{source === 'saved' ? 'Saved Jobs' : 'Matching Jobs'}</h3>
          <div className="meta" style={{ marginTop: 0 }}>
            {source === 'saved' ? (
              <>
                {data.jobs.length} saved for this profile · {strong} strong
              </>
            ) : (
              <>
                {data.new_count > 0 ? (
                  <span className="new-count">
                    +{data.new_count} new {data.new_count === 1 ? 'job' : 'jobs'}
                  </span>
                ) : (
                  <span>No new jobs since the last refresh</span>
                )}{' '}
                · {data.jobs.length} total · {strong} strong
              </>
            )}
          </div>
        </div>

        {data.jobs.length > 0 && (
          <div className="jobs-controls">
            <button
              className={`toggle-chip ${verifiedOnly ? 'on' : ''}`}
              onClick={() => setVerifiedOnly((v) => !v)}
            >
              ✓ Verified only
            </button>
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              {Object.entries(SORTS).map(([k, v]) => (
                <option key={k} value={k}>
                  {v.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {data.jobs.length === 0 && <div className="empty-state">No jobs matched your filters.</div>}
      {data.jobs.length > 0 && jobs.length === 0 && (
        <div className="empty-state">No payment-verified jobs in this batch.</div>
      )}

      {jobs.map((job) => (
        <JobCard key={job.id ?? job.title} job={job} profile={profile} />
      ))}
    </div>
  )
}
