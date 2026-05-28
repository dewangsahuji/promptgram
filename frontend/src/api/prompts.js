import client from './client'

export const listPrompts = (page = 1, limit = 20) =>
  client.get('/prompts/', { params: { page, limit } }).then(r => r.data)

export const getTrending = () =>
  client.get('/prompts/trending').then(r => r.data)

export const getPrompt = (id) =>
  client.get(`/prompts/${id}`).then(r => r.data)

export const createPrompt = (data) =>
  client.post('/prompts/', data).then(r => r.data)

export const updatePrompt = (id, data) =>
  client.patch(`/prompts/${id}`, data).then(r => r.data)

export const deletePrompt = (id) =>
  client.delete(`/prompts/${id}`)

export const getImages = (promptId) =>
  client.get(`/images/prompt/${promptId}`).then(r => r.data)

export const uploadImage = (promptId, file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return client.post(`/images/upload?prompt_id=${promptId}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => onProgress && onProgress(Math.round(e.loaded * 100 / e.total))
  }).then(r => r.data)
}

export const semanticSearch = (query, limit = 20) =>
  client.post('/ai/search', { query, limit }).then(r => r.data)
