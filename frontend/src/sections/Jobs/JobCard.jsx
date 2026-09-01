import { useState } from 'react'
import ErrorBox from '../../components/ErrorBox'
import { evaluateJob, generateProposal } from '../../api/client'
import {
  buildJobEvaluateRequest,
  buildProposalRequest,
  formatBudget,
  formatMoney,
  formatPosted,
  scoreTier,
  timeAgo,
} from './jobMapping'
import JobEvaluationResult from './JobEvaluationResult'
import ProposalResult from './ProposalResult'

export default function JobCard({ job, profile }) {
  const [evalState, setEvalState] = useState({ loading: false, error: null, result: null })
  const [proposalState, setProposalState] = useState({ loading: false, error: null, result: null })
  const [expanded, setExpanded] = useState(false)

  const handleEvaluate = async () => {
    setEvalState({ loading: true, error: null, result: null })
    try {
      const data = await evaluateJob(buildJobEvaluateRequest(job, profile.model))
      setEvalState({ loading: false, error: null, result: data })
    } catch (e) {
      setEvalState({ loading: false, error: e.message, result: null })
    }
  }

  const handleGenerateProposal = async () => {
    if (!profile.niche.trim()) {
      alert('Set a Niche / Positioning on your profile first.')
      return
    }
    setProposalState({ loading: true, error: null, result: null })
    try {
      const data = await generateProposal(buildProposalRequest(job, profile))
      setProposalState({ loading: false, error: null, result: data })
    } catch (e) {
      setProposalState({ loading: false, error: e.message, result: null })
    }
  }

  const budget = formatBudget(job)
  const spent = formatMoney(job.total_spent)
  const posted = formatPosted(job.date_posted)
  const age = timeAgo(job.date_posted)
  const tier = scoreTier(job.job_score)
  // Roughly the point where the text exceeds the 3-line clamp at card width.
  const longDescription = (job.description || '').length > 200
  const clamped = longDescription && !expanded

  return (
    <div className="job-card">
      <div className="job-head">
        {job.job_score != null && (
          <div className={`job-score ${tier}`} title="Apify job score (0-100)">
            <span className="n">{Math.round(job.job_score)}</span>
            <span className="l">score</span>
          </div>
        )}

        <div className="job-head-text">
          <h4>
            {job.url ? (
              <a href={job.url} target="_blank" rel="noreferrer">
                {job.title}
              </a>
            ) : (
              job.title
            )}
          </h4>
          <div className="job-headline">
            {budget && <span className="job-budget">{budget}</span>}
            {job.price_type && <span>{job.price_type}</span>}
            {job.experience_level && <span>{job.experience_level}</span>}
            {age && <span title={posted || ''}>{age}</span>}
          </div>
        </div>
      </div>

      {job.description && (
        <div className={`job-desc ${clamped ? 'clamped' : ''}`}>{job.description}</div>
      )}
      {longDescription && (
        <button className="link-btn" onClick={() => setExpanded((v) => !v)}>
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}

      <div className="job-meta-row">
        {job.buyer_payment_verified ? (
          <span className="chip-good">✓ Payment verified</span>
        ) : (
          <span className="chip-warn">Unverified payment</span>
        )}
        {job.buyer_score != null && <span>★ {job.buyer_score.toFixed(2)}</span>}
        {job.hire_rate != null && <span>{job.hire_rate}% hire rate</span>}
        {spent && <span>{spent} spent</span>}
        {job.client_location && <span>{job.client_location}</span>}
      </div>

      {job.skills && <div className="job-skills">{job.skills}</div>}

      <div className="job-actions">
        <button onClick={handleEvaluate} disabled={evalState.loading}>
          {evalState.loading ? (
            <>
              <span className="spinner" />
              Evaluating...
            </>
          ) : (
            'Evaluate'
          )}
        </button>
        <button className="btn-secondary" onClick={handleGenerateProposal} disabled={proposalState.loading}>
          {proposalState.loading ? (
            <>
              <span className="spinner" />
              Generating...
            </>
          ) : (
            'Generate Proposal'
          )}
        </button>
        {job.url && (
          <a className="job-open" href={job.url} target="_blank" rel="noreferrer">
            Open on Upwork ↗
          </a>
        )}
      </div>

      {evalState.error && <ErrorBox message={evalState.error} />}
      {evalState.result && <JobEvaluationResult data={evalState.result} />}

      {proposalState.error && <ErrorBox message={proposalState.error} />}
      {proposalState.result && <ProposalResult data={proposalState.result} />}
    </div>
  )
}
