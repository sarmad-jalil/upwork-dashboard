import { useCallback, useEffect, useState } from 'react'
import {
  listProfiles,
  createProfile,
  updateProfile,
  deleteProfile,
  activateProfile,
} from '../api/client'

/** Profiles are shared across both tabs — the Profiles tab edits them, the Jobs
 *  tab scrapes with whichever one is active — so the state lives here. */
export default function useProfiles() {
  const [profiles, setProfiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const data = await listProfiles()
      setProfiles(data.profiles)
      setError(null)
      return data.profiles
    } catch (e) {
      setError(e.message)
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // False positive: refresh() suspends at `await listProfiles()` before any
    // setState runs, so nothing is set synchronously during this effect.
    // eslint-disable-next-line react/set-state-in-effect
    refresh()
  }, [refresh])

  const create = useCallback(
    async (payload) => {
      await createProfile(payload)
      await refresh()
    },
    [refresh],
  )

  const update = useCallback(
    async (id, payload) => {
      await updateProfile(id, payload)
      await refresh()
    },
    [refresh],
  )

  const remove = useCallback(
    async (id) => {
      await deleteProfile(id)
      await refresh()
    },
    [refresh],
  )

  const activate = useCallback(
    async (id) => {
      await activateProfile(id)
      await refresh()
    },
    [refresh],
  )

  const activeProfile = profiles.find((p) => p.is_active) || null

  return {
    profiles,
    activeProfile,
    loading,
    error,
    setError,
    refresh,
    create,
    update,
    remove,
    activate,
  }
}
