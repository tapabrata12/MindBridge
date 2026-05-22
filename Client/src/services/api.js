// File: Client/src/services/api.js

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim() || ''

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

const readResponseBody = async (response) => {
  const text = await response.text()

  if (!text) {
    return null
  }

  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

const getErrorMessage = (payload, fallback) => {
  if (!payload) {
    return fallback
  }

  if (typeof payload === 'string') {
    return payload
  }

  if (typeof payload.detail === 'string') {
    return payload.detail
  }

  if (Array.isArray(payload.detail)) {
    return payload.detail.map((item) => item.msg || item.type).filter(Boolean).join(', ')
  }

  return fallback
}

export const apiRequest = async (path, { method = 'GET', token, body } = {}) => {
  const headers = {
    Accept: 'application/json',
  }

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  const payload = await readResponseBody(response)

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(payload, `Request failed with status ${response.status}`),
      response.status,
      payload,
    )
  }

  return payload
}

export const api = {
  health: () => apiRequest('/health'),
  register: (body) => apiRequest('/api/auth/register', { method: 'POST', body }),
  login: (body) => apiRequest('/api/auth/login', { method: 'POST', body }),
  me: (token) => apiRequest('/api/auth/me', { token }),
  getProfile: (token) => apiRequest('/api/profile', { token }),
  updateProfile: (token, body) => apiRequest('/api/profile', { method: 'PUT', token, body }),
  startPhq9: (token, body) =>
    apiRequest('/api/assessment/phq9/conversation/start', { method: 'POST', token, body }),
  answerPhq9: (token, body) =>
    apiRequest('/api/assessment/phq9/conversation/answer', { method: 'POST', token, body }),
  getPhq9History: (token) => apiRequest('/api/assessment/phq9/history?limit=5&skip=0', { token }),
  logout: (token) => apiRequest('/api/auth/logout', { method: 'POST', token }),
}
