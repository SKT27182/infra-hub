import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getMe, type InfraUser } from '@/lib/api'

interface AuthContextType {
  user: InfraUser | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user: InfraUser) => void
  logout: () => void
  refreshUser: () => Promise<void>
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<InfraUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const t = localStorage.getItem('auth_token')
    if (!t) return
    const me = await getMe()
    setUser(me)
    localStorage.setItem('auth_user', JSON.stringify(me))
  }, [])

  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token')
    const savedUser = localStorage.getItem('auth_user')

    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser) as InfraUser)
      void refreshUser().catch(() => {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
        setToken(null)
        setUser(null)
      })
    }
    setIsLoading(false)
  }, [refreshUser])

  const login = (newToken: string, newUser: InfraUser) => {
    setToken(newToken)
    setUser(newUser)
    localStorage.setItem('auth_token', newToken)
    localStorage.setItem('auth_user', JSON.stringify(newUser))
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        login,
        logout,
        refreshUser,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
