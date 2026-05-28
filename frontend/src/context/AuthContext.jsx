import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('pg_token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      // Decode JWT payload (no verification needed — server does that)
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        setUser({ id: payload.sub, token })
      } catch {
        setToken(null)
        localStorage.removeItem('pg_token')
      }
    }
    setLoading(false)
  }, [token])

  const login = (newToken) => {
    localStorage.setItem('pg_token', newToken)
    setToken(newToken)
  }

  const logout = () => {
    localStorage.removeItem('pg_token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading, isAuth: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
