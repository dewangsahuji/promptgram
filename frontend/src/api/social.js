import client from './client'

export const toggleLike   = (promptId) => client.post(`/like/${promptId}`).then(r => r.data)
export const getLikeCount = (promptId) => client.get(`/like/${promptId}/count`).then(r => r.data)

export const getComments  = (promptId) => client.get(`/comment/${promptId}`).then(r => r.data)
export const addComment   = (promptId, body) => client.post(`/comment/${promptId}`, { body }).then(r => r.data)
export const deleteComment = (id)      => client.delete(`/comment/${id}`)

export const toggleFollow     = (userId) => client.post(`/follow/${userId}`).then(r => r.data)
export const getFollowers     = (userId) => client.get(`/follow/${userId}/followers`).then(r => r.data)
export const getFollowing     = (userId) => client.get(`/follow/${userId}/following`).then(r => r.data)

export const createCollection = (data)  => client.post('/collections/', data).then(r => r.data)
export const getMyCollections = ()      => client.get('/collections/my').then(r => r.data)

export const getUserProfile   = (id)   => client.get(`/users/${id}`).then(r => r.data)
export const getUserPrompts   = (id)   => client.get(`/users/${id}/prompts`).then(r => r.data)
