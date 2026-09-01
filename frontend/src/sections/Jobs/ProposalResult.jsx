import CopyButton from '../../components/CopyButton'

export default function ProposalResult({ data }) {
  return (
    <div className="result">
      <h3>Generated Proposal</h3>

      <div className="proposal-box">{data.proposal}</div>
      <CopyButton text={data.proposal} />

      <div className="section-label" style={{ marginTop: 16 }}>
        Opening Question
      </div>
      <div style={{ fontSize: 13, color: 'var(--accent)', fontStyle: 'italic' }}>
        {data.opening_question}
      </div>

      <div className="section-label">Micro-Win / Insight Used</div>
      <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{data.micro_win}</div>

      <div className="meta">
        Words: {data.word_count} · Model: {data.model_used} · Provider: {data.provider}
      </div>
    </div>
  )
}
