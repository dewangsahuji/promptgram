import client from './client'

export const signup = (data) =>
  client.post('/auth/signup', data).then(r => r.data)

export const login = (email, password) => {
  const form = new FormData()
  form.append('username', email)
  form.append('password', password)
  return client.post('/auth/login', form).then(r => r.data)
}

export const getMe = () =>
  client.get('/auth/me').then(r => r.data)

export const logout = () =>
  client.post('/auth/logout').then(r => r.data)

export const getUserById = (id) =>
  client.get(`/auth/users/${id}`).then(r => r.data)
