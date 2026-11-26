import { apiRequest } from './client'

export function listNews(authorId = null) {
  const query = authorId ? `?author_id=${encodeURIComponent(authorId)}` : ''
  return apiRequest(`/news${query}`)
}

export function getNews(newsId) {
  return apiRequest(`/news/${newsId}`)
}

export function createNews({ title, content, cover = null }) {
  const payload = { title, content }
  if (cover) payload.cover = cover
  return apiRequest('/news', {
    method: 'POST',
    body: payload,
  })
}

export function updateNews(newsId, payload) {
  return apiRequest(`/news/${newsId}`, {
    method: 'PATCH',
    body: payload,
  })
}

export function deleteNews(newsId) {
  return apiRequest(`/news/${newsId}`, {
    method: 'DELETE',
  })
}

export function listNewsComments(newsId) {
  return apiRequest(`/news/${newsId}/comments`)
}
