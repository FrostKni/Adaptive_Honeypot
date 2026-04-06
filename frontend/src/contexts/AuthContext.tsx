import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { getApiUrl } from '../config/env'
import { toast } from '../stores/toastStore'

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
      fetch(getApiUrl('/api/v1/auth/me'), {
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
      const res = await fetch(getApiUrl('/api/v1/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      if (!res.ok) {
        toast.error('Login Failed', 'Invalid username or password')
        return false
      }

      const data = await res.json()
      localStorage.setItem('token', data.access_token)
      setToken(data.access_token)

      // Fetch user info
      const userRes = await fetch(getApiUrl('/api/v1/auth/me'), {
        headers: { 'Authorization': `Bearer ${data.access_token}` }
      })
      
      if (userRes.ok) {
        const userData = await userRes.json()
        setUser(userData)
        toast.success('Welcome back!', `Logged in as ${userData.subject || 'Admin'}`)
        return true
      } else {
        // If /auth/me fails, still consider login successful since we have a token
        // The user can still access protected routes
        console.error('Failed to fetch user info, but login was successful')
        setUser({ subject: username, auth_type: 'jwt', scopes: [], is_admin: true })
        toast.success('Welcome back!', `Logged in as ${username}`)
        return true
      }
    } catch (error) {
      console.error('Login error:', error)
      toast.error('Connection Error', 'Unable to connect to the server')
      return false
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
    toast.info('Signed Out', 'You have been logged out successfully')
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