export default function SubmitButton({ loading, loadingLabel = 'Working...', label, onClick, disabled = false }) {
  return (
    <button onClick={onClick} disabled={loading || disabled}>
      {loading ? (
        <>
          <span className="spinner" />
          {loadingLabel}
        </>
      ) : (
        label
      )}
    </button>
  )
}
