import { useState } from 'react'
import useProfiles from './hooks/useProfiles'
import JobsTab from './sections/Jobs/JobsTab'
import ProfilesTab from './sections/Profiles/ProfilesTab'

const TABS = [
  { key: 'jobs', label: 'Jobs' },
  { key: 'profiles', label: 'Profiles' },
]

export default function App() {
  const [tab, setTab] = useState('jobs')
  const profileState = useProfiles()

  return (
    <>
      <header>
        <h1>Upwork Dashboard</h1>
        <span>AI-Powered</span>

        <nav className="main-nav">
          {TABS.map((t) => (
            <button
              key={t.key}
              className={`nav-link ${tab === t.key ? 'active' : ''}`}
              onClick={() => setTab(t.key)}
            >
              {t.label}
              {t.key === 'profiles' && profileState.profiles.length > 0 && (
                <span className="count-pill">{profileState.profiles.length}</span>
              )}
            </button>
          ))}
        </nav>

        {profileState.activeProfile && (
          <span className="header-active" title={profileState.activeProfile.niche}>
            ● {profileState.activeProfile.name}
          </span>
        )}
      </header>

      <div className="content">
        {tab === 'jobs' ? (
          <JobsTab
            profiles={profileState.profiles}
            activeProfile={profileState.activeProfile}
            profilesLoading={profileState.loading}
            onSelectProfile={profileState.activate}
            onGoToProfiles={() => setTab('profiles')}
          />
        ) : (
          <ProfilesTab {...profileState} />
        )}
      </div>
    </>
  )
}
