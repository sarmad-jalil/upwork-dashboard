export default function JobEvaluationResult({ data }) {
  const isApply = data.recommendation === 'apply'

  return (
    <div className="result">
      <h3>Evaluation Result</h3>

      <div>
        <span className={`badge ${isApply ? 'apply' : 'skip'}`}>
          {isApply ? '✓ APPLY' : '✕ SKIP'}
        </span>
        <span style={{ fontSize: 13, color: 'var(--text-muted)', marginLeft: 10 }}>
          Score: {data.score}/10
        </span>
      </div>
      <div style={{ fontSize: 13, marginBottom: 12, marginTop: 8 }}>{data.reason}</div>

      <div className="row">
        <div>
          <div className="section-label">Green Flags</div>
          <ul className="green">
            {data.green_flags.map((flag, i) => (
              <li key={i}>{flag}</li>
            ))}
          </ul>
        </div>
        <div>
          <div className="section-label">Red Flags</div>
          <ul className="red">
            {data.red_flags.map((flag, i) => (
              <li key={i}>{flag}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="section-label">Proposal Tips (if you apply)</div>
      <ul className="neutral">
        {data.proposal_tips.map((tip, i) => (
          <li key={i}>{tip}</li>
        ))}
      </ul>

      <div className="meta">
        Model: {data.model_used} · Provider: {data.provider}
      </div>
    </div>
  )
}
