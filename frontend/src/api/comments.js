import { apiRequest } from './client'

export function createComment({ news_id, text }) {
  return apiRequest('/comments', {
    method: 'POST',
    body: { news_id: Number(news_id), text },
  })
}

export function updateComment(commentId, text) {
  return apiRequest(`/comments/${commentId}`, {
    method: 'PATCH',
    body: { text },
  })
}

export function deleteComment(commentId) {
  return apiRequest(`/comments/${commentId}`, {
    method: 'DELETE',
  })
}
