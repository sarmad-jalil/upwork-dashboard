import { useRef, useState } from 'react'
import ErrorBox from '../../components/ErrorBox'

const emptyForm = {
  name: '',
  niche: '',
  keywords: '',
  exclude_keywords: '',
  experience: '',
  model: 'groq',
  min_job_score: 40,
}

/** Profile record -> form fields (arrays become comma-separated text). */
function formFromProfile(p) {
  return {
    name: p.name,
    niche: p.niche,
    keywords: p.keywords.join(', '),
    exclude_keywords: p.exclude_keywords.join(', '),
    experience: p.experience || '',
    model: p.model,
    min_job_score: p.min_job_score,
  }
}

const MAX_VISIBLE_KEYWORDS = 10

function ProfileCard({ profile, onSelect, onEdit, onDelete }) {
  const shown = profile.keywords.slice(0, MAX_VISIBLE_KEYWORDS)
  const hidden = profile.keywords.length - shown.length

  return (
    <div className={`profile-card ${profile.is_active ? 'active' : ''}`}>
      <div className="profile-card-body">
        <div className="profile-name">
          {profile.name}
          {profile.is_active && <span className="active-tag">Active</span>}
        </div>
        <div className="profile-niche">{profile.niche}</div>

        {shown.length > 0 && (
          <div className="profile-tags">
            {shown.map((k) => (
              <span key={k}>{k}</span>
            ))}
            {hidden > 0 && (
              <span className="more" title={profile.keywords.join(', ')}>
                +{hidden} more
              </span>
            )}
          </div>
        )}

        {profile.exclude_keywords.length > 0 && (
          <div className="profile-excludes">
            Excluding: {profile.exclude_keywords.join(', ')}
          </div>
        )}

        {profile.experience && <div className="profile-exp">{profile.experience}</div>}

        <div className="profile-foot">
          {profile.model} · min score {profile.min_job_score} · {profile.keywords.length} keywords
        </div>
      </div>

      <div className="profile-actions">
        {!profile.is_active && (
          <button className="btn-select" onClick={() => onSelect(profile.id)}>
            Set Active
          </button>
        )}
        <button className="btn-select" onClick={() => onEdit(profile)}>
          Edit
        </button>
        <button className="btn-delete" onClick={() => onDelete(profile.id, profile.name)}>
          Delete
        </button>
      </div>
    </div>
  )
}

export default function ProfilesTab({
  profiles,
  loading,
  error,
  setError,
  create,
  update,
  remove,
  activate,
}) {
  const [form, setForm] = useState(emptyForm)
  const [creating, setCreating] = useState(false)
  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState(null) // null = creating a new profile
  const formRef = useRef(null)

  const showForm = formOpen || (!loading && profiles.length === 0)
  const isEditing = editingId != null

  const closeForm = () => {
    setFormOpen(false)
    setEditingId(null)
    setForm(emptyForm)
  }

  const handleEdit = (profile) => {
    setForm(formFromProfile(profile))
    setEditingId(profile.id)
    setFormOpen(true)
    setError(null)
    // The form sits below the grid, so bring it into view when it opens.
    requestAnimationFrame(() => formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
  }

  const handleSubmit = async () => {
    if (!form.name.trim() || !form.niche.trim()) {
      alert('Profile name and niche are required.')
      return
    }
    const payload = {
      name: form.name.trim(),
      niche: form.niche.trim(),
      keywords: form.keywords.split(',').map((s) => s.trim()).filter(Boolean),
      exclude_keywords: form.exclude_keywords.split(',').map((s) => s.trim()).filter(Boolean),
      experience: form.experience.trim() || null,
      model: form.model,
      min_job_score: parseInt(form.min_job_score, 10) || 0,
    }

    setCreating(true)
    setError(null)
    try {
      if (isEditing) {
        await update(editingId, payload)
      } else {
        await create(payload)
      }
      closeForm()
    } catch (e) {
      setError(e.message)
    } finally {
      setCreating(false)
    }
  }

  const handleSelect = async (id) => {
    try {
      await activate(id)
    } catch (e) {
      alert('Failed to set active profile: ' + e.message)
    }
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete profile "${name}"? This cannot be undone.`)) return
    try {
      await remove(id)
    } catch (e) {
      alert('Failed to delete profile: ' + e.message)
    }
  }

  return (
    <div>
      <div className="card">
        <div className="card-head">
          <div>
            <h2>Profiles</h2>
            <p style={{ marginBottom: 0 }}>
              Each profile is a niche. The active one decides what the Jobs tab scrapes.
            </p>
          </div>
          {!showForm && (
            <button
              onClick={() => {
                setForm(emptyForm)
                setEditingId(null)
                setFormOpen(true)
              }}
            >
              + New Profile
            </button>
          )}
        </div>

        {error && <ErrorBox message={error} />}

        {loading && <div className="empty-hint">Loading profiles...</div>}

        {!loading && profiles.length > 0 && (
          <div className="profiles-grid" style={{ marginTop: 24 }}>
            {profiles.map((p) => (
              <ProfileCard
                key={p.id}
                profile={p}
                onSelect={handleSelect}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {!loading && profiles.length === 0 && !showForm && (
          <div className="empty-hint">No profiles yet — create one to get started.</div>
        )}
      </div>

      {showForm && (
        <div className="card" ref={formRef}>
          <div className="card-head">
            <div>
              <h2>{isEditing ? `Edit "${form.name || 'Profile'}"` : 'New Profile'}</h2>
              <p style={{ marginBottom: 0 }}>
                Keywords drive the Upwork search. The niche is used when generating proposals.
              </p>
            </div>
          </div>

          <div style={{ marginTop: 24 }}>
            <div className="row">
              <div>
                <label>Profile Name</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Shopify DTC"
                />
              </div>
              <div>
                <label>Niche / Positioning</label>
                <input
                  type="text"
                  value={form.niche}
                  onChange={(e) => setForm({ ...form, niche: e.target.value })}
                  placeholder='e.g. "Shopify store designer for DTC brands"'
                />
              </div>
            </div>

            <label>
              Keywords <span className="optional">(comma-separated — these drive the job search)</span>
            </label>
            <input
              type="text"
              value={form.keywords}
              onChange={(e) => setForm({ ...form, keywords: e.target.value })}
              placeholder="Shopify, e-commerce, conversion"
            />

            <label>
              Exclude Keywords <span className="optional">(optional)</span>
            </label>
            <input
              type="text"
              value={form.exclude_keywords}
              onChange={(e) => setForm({ ...form, exclude_keywords: e.target.value })}
              placeholder="Wix, Squarespace"
            />

            <label>
              Relevant Experience <span className="optional">(optional, used for proposals)</span>
            </label>
            <textarea
              rows={2}
              value={form.experience}
              onChange={(e) => setForm({ ...form, experience: e.target.value })}
              placeholder="e.g. Redesigned 3 Shopify stores, avg 35% conversion lift"
            />

            <div className="row">
              <div>
                <label>Model (used for Evaluate &amp; Generate Proposal)</label>
                <select value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })}>
                  <option value="groq">Groq (Free)</option>
                  <option value="mistral">Mistral</option>
                  <option value="claude">Claude</option>
                </select>
              </div>
              <div>
                <label>
                  Min Job Score <span className="optional">(0-100)</span>
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={form.min_job_score}
                  onChange={(e) => setForm({ ...form, min_job_score: e.target.value })}
                />
              </div>
            </div>

            <div className="form-actions">
              <button onClick={handleSubmit} disabled={creating}>
                {creating ? (
                  <>
                    <span className="spinner" />
                    {isEditing ? 'Saving...' : 'Creating...'}
                  </>
                ) : isEditing ? (
                  'Save Changes'
                ) : (
                  'Create Profile'
                )}
              </button>
              {profiles.length > 0 && (
                <button className="btn-secondary" onClick={closeForm}>
                  Cancel
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
