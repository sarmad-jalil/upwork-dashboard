// Empty = same origin. The backend serves this build, and `npm run dev` proxies
// API paths to it (see vite.config.js), so no absolute URL is needed either way.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || 'Request failed')
  }
  return data
}

export const evaluateJob = (payload) =>
  request('/job/evaluate', { method: 'POST', body: JSON.stringify(payload) })

export const generateProposal = (payload) =>
  request('/proposal/generate', { method: 'POST', body: JSON.stringify(payload) })

export const scrapeJobs = (params = {}) => {
  const query = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''))
  ).toString()
  return request(`/jobs/scrape${query ? `?${query}` : ''}`, { method: 'GET' })
}

export const listProfiles = () => request('/profiles')

export const createProfile = (payload) =>
  request('/profiles', { method: 'POST', body: JSON.stringify(payload) })

export const updateProfile = (id, payload) =>
  request(`/profiles/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })

export const deleteProfile = (id) => request(`/profiles/${id}`, { method: 'DELETE' })

export const activateProfile = (id) => request(`/profiles/${id}/activate`, { method: 'POST' })

export const listProfileJobs = (id) => request(`/profiles/${id}/jobs`)
