import axios from 'axios'

const client = axios.create({ baseURL: '/api' })

// Attach JWT from localStorage to every request
client.interceptors.request.use(cfg => {
  const token = localStorage.getItem('pg_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// On 401 — clear token
client.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('pg_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client
