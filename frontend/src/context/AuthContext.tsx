import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getMe, logoutUser, type InfraUser } from '@/lib/api'

interface AuthContextType {
  user: InfraUser | null
  isAuthenticated: boolean
  login: (user: InfraUser) => void
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<InfraUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const me = await getMe()
    setUser(me)
  }, [])

  useEffect(() => {
    void refreshUser()
      .catch(() => {
        setUser(null)
      })
      .finally(() => setIsLoading(false))
  }, [refreshUser])

  const login = (newUser: InfraUser) => {
    setUser(newUser)
  }

  const logout = async () => {
    try {
      await logoutUser()
    } finally {
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
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

// This hook intentionally shares the provider's private context.
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
