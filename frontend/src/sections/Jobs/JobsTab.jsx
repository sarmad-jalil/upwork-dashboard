import { useCallback, useEffect, useState } from 'react'
import SubmitButton from '../../components/SubmitButton'
import ErrorBox from '../../components/ErrorBox'
import { scrapeJobs, listProfileJobs } from '../../api/client'
import JobsList from './JobsList'

export default function JobsTab({
  profiles,
  activeProfile,
  profilesLoading,
  onSelectProfile,
  onGoToProfiles,
}) {
  const [loading, setLoading] = useState(false)
  const [switching, setSwitching] = useState(false)
  const [error, setError] = useState(null)
  // Tagged with the profile it belongs to, so switching profiles never shows
  // the previous profile's jobs while the new ones load.
  const [entry, setEntry] = useState(null) // { profileId, data, source }

  const activeId = activeProfile?.id ?? null

  // Jobs already scraped for this profile live in Supabase — show them straight
  // away so opening the dashboard doesn't require paying for a fresh scrape.
  useEffect(() => {
    if (!activeId) return
    let cancelled = false
    listProfileJobs(activeId)
      .then((data) => !cancelled && setEntry({ profileId: activeId, data, source: 'saved' }))
      .catch((e) => !cancelled && setError(e.message))
    return () => {
      cancelled = true
    }
  }, [activeId])

  // Refresh = scrape the newest jobs for this profile. `since`/`limit` are left
  // to the backend defaults (last 24h, JOBS_DEFAULT_LIMIT).
  const handleRefresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await scrapeJobs({ profile_id: activeId ?? undefined })
      setEntry({ profileId: activeId, data, source: 'scrape' })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [activeId])

  const handleProfileChange = async (e) => {
    const id = parseInt(e.target.value, 10)
    if (!id || id === activeId) return
    setSwitching(true)
    setError(null)
    try {
      await onSelectProfile(id)
    } catch (err) {
      setError(err.message)
    } finally {
      setSwitching(false)
    }
  }

  const current = entry && entry.profileId === activeId ? entry : null
  const result = current?.data ?? null
  const source = current?.source ?? null
  const hasJobs = result && result.jobs.length > 0
  const loadingSaved = activeId != null && current == null && !error

  // No profile at all — the Jobs tab can't do anything, so point at the fix.
  if (!profilesLoading && !activeProfile) {
    return (
      <div className="card">
        <div className="empty-state big">
          <div className="empty-icon">👤</div>
          <div className="empty-title">No active profile</div>
          <div style={{ marginBottom: 20 }}>
            Jobs are scraped for a profile&apos;s niche. Create one to get started.
          </div>
          <button onClick={onGoToProfiles}>Go to Profiles</button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="card">
        <div className="card-head">
          <div>
            <h2>Jobs</h2>
            <p style={{ marginBottom: 0 }}>
              {activeProfile && <>Scraping for &quot;{activeProfile.niche}&quot;</>}
            </p>
          </div>

          <div className="profile-picker">
            <label htmlFor="job-profile">Profile</label>
            <select
              id="job-profile"
              value={activeId ?? ''}
              onChange={handleProfileChange}
              disabled={switching || loading}
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            {switching && <span className="spinner" />}
            <button className="copy-btn" onClick={onGoToProfiles}>
              Manage
            </button>
            <SubmitButton
              loading={loading}
              loadingLabel="Refreshing..."
              label="↻ Refresh"
              onClick={handleRefresh}
              disabled={!activeProfile || switching}
            />
          </div>
        </div>

        <div className="scrape-hint">
          <strong>Refresh</strong> scrapes the newest Upwork jobs for this profile — it bills your
          Apify account each time. Results are saved to Supabase (latest 50 per profile).
        </div>
      </div>

      {error && (
        <div className="result">
          <ErrorBox message={error} />
        </div>
      )}

      {/* A scrape takes several seconds. Without a loud in-page state the old
          list just sits there and the refresh looks like it did nothing. */}
      {loading && (
        <div className="scraping-banner">
          <span className="spinner" />
          <span>
            Scraping the latest Upwork jobs{activeProfile ? ` for ${activeProfile.name}` : ''}…
            <span className="muted"> this usually takes 5–15 seconds.</span>
          </span>
        </div>
      )}

      {loadingSaved && !loading && (
        <div className="result">
          <div className="empty-state">
            <span className="spinner" />
            Loading saved jobs...
          </div>
        </div>
      )}

      {!loadingSaved && !loading && !error && activeProfile && !hasJobs && (
        <div className="result">
          <div className="empty-state big">
            <div className="empty-icon">🔍</div>
            <div className="empty-title">No jobs yet for {activeProfile.name}</div>
            <div>
              Hit <strong>↻ Refresh</strong> to pull the latest Upwork posts for this niche.
            </div>
          </div>
        </div>
      )}

      {/* Stale results stay readable but visibly dimmed while a refresh runs. */}
      {!loadingSaved && hasJobs && (
        <div className={loading ? 'is-stale' : ''}>
          <JobsList data={result} profile={activeProfile} source={source} />
        </div>
      )}
    </div>
  )
}
