import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  subject: string
  auth_type: string
  scopes: string[]
  is_admin: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if we have a token and validate it
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${storedToken}`
        }
      })
        .then(res => {
          if (res.ok) return res.json()
          throw new Error('Invalid token')
        })
        .then(data => {
          setUser(data)
          setToken(storedToken)
        })
        .catch(() => {
          localStorage.removeItem('token')
          setToken(null)
          setUser(null)
        })
        .finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      if (!res.ok) return false

      const data = await res.json()
      localStorage.setItem('token', data.access_token)
      setToken(data.access_token)

      // Fetch user info
      const userRes = await fetch('/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${data.access_token}` }
      })
      
      if (userRes.ok) {
        const userData = await userRes.json()
        setUser(userData)
      }

      return true
    } catch {
      return false
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}