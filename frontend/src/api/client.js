const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const ACCESS_TOKEN_KEY = 'news_access_token'
const REFRESH_TOKEN_KEY = 'news_refresh_token'

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

export function getStoredTokens() {
  return {
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  }
}

export function saveStoredTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
  if (refresh_token) localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
}

export function clearStoredTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

let refreshPromise = null

async function refreshAccessToken() {
  const { refreshToken } = getStoredTokens()
  if (!refreshToken) return null

  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (res) => {
        if (!res.ok) {
          clearStoredTokens()
          return null
        }
        const data = await res.json()
        saveStoredTokens(data)
        return data.access_token
      })
      .catch(() => {
        clearStoredTokens()
        return null
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

export async function apiRequest(path, options = {}) {
  const { auth = true, retryOn401 = true, headers = {}, body, ...rest } = options
  const { accessToken } = getStoredTokens()

  const requestHeaders = { ...headers }
  if (body !== undefined && !requestHeaders['Content-Type']) {
    requestHeaders['Content-Type'] = 'application/json'
  }
  if (auth && accessToken) {
    requestHeaders.Authorization = `Bearer ${accessToken}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
    body: body !== undefined && typeof body !== 'string' ? JSON.stringify(body) : body,
  })

  if (response.status === 401 && auth && retryOn401 && getStoredTokens().refreshToken) {
    const newAccessToken = await refreshAccessToken()
    if (newAccessToken) {
      return apiRequest(path, { ...options, retryOn401: false })
    }
  }

  if (response.status === 204) {
    return null
  }

  const text = await response.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!response.ok) {
    const message =
      (data && typeof data === 'object' && (data.detail || data.message)) ||
      `HTTP ${response.status}`
    throw new ApiError(
      typeof message === 'string' ? message : JSON.stringify(message),
      response.status,
      data,
    )
  }

  return data
}

export { API_BASE_URL }
