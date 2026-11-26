import { API_BASE_URL, apiRequest } from './client'

export function login(email, password) {
  return apiRequest('/auth/login', {
    method: 'POST',
    auth: false,
    body: { email, password },
  })
}

export function register({ name, email, password, avatar = null }) {
  const payload = { name, email, password }
  if (avatar) payload.avatar = avatar
  return apiRequest('/auth/register', {
    method: 'POST',
    auth: false,
    body: payload,
  })
}

export function logout(refreshToken) {
  return apiRequest('/auth/logout', {
    method: 'POST',
    auth: false,
    body: { refresh_token: refreshToken },
  })
}

export function getMe() {
  return apiRequest('/users/me')
}

export function getSessions() {
  return apiRequest('/auth/sessions')
}

export function getGithubLoginUrl() {
  return `${API_BASE_URL}/auth/github/login`
}
