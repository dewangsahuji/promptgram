import client from './client'

export const listPrompts = (page = 1, limit = 20) =>
  client.get('/prompts/', { params: { page, limit } }).then(r => r.data)

export const getTrending = () =>
  client.get('/prompts/trending').then(r => r.data)

export const getPrompt = (id) =>
  client.get(`/prompts/${id}`).then(r => r.data)

export const createPrompt = (data, onProgress) => {
  const config = {}
  if (data instanceof FormData) {
    config.headers = { 'Content-Type': 'multipart/form-data' }
    config.onUploadProgress = e => onProgress && onProgress(Math.round(e.loaded * 100 / e.total))
  }
  return client.post('/prompts/', data, config).then(r => r.data)
}

export const updatePrompt = (id, data) =>
  client.patch(`/prompts/${id}`, data).then(r => r.data)

export const deletePrompt = (id) =>
  client.delete(`/prompts/${id}`)

export const getImages = (promptId) =>
  client.get(`/images/prompt/${promptId}`).then(r => r.data)

export const searchPrompts = (query, page = 1, limit = 20) =>
  client.get('/prompts/search', { params: { q: query, page, limit } }).then(r => r.data)
