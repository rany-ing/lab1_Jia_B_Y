import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import * as authApi from '../api/auth'
import { clearStoredTokens, getStoredTokens, saveStoredTokens } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadCurrentUser = useCallback(async () => {
    const { accessToken, refreshToken } = getStoredTokens()
    if (!accessToken && !refreshToken) {
      setUser(null)
      setLoading(false)
      return null
    }
    try {
      const me = await authApi.getMe()
      setUser(me)
      return me
    } catch {
      clearStoredTokens()
      setUser(null)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCurrentUser()
  }, [loadCurrentUser])

  const login = useCallback(async (email, password) => {
    const tokens = await authApi.login(email, password)
    saveStoredTokens(tokens)
    const me = await authApi.getMe()
    setUser(me)
    return me
  }, [])

  const register = useCallback(
    async ({ name, email, password, avatar }) => {
      await authApi.register({ name, email, password, avatar })
      return login(email, password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    const { refreshToken } = getStoredTokens()
    try {
      if (refreshToken) {
        await authApi.logout(refreshToken)
      }
    } catch {
      // Ignore network/revocation errors on local logout
    } finally {
      clearStoredTokens()
      setUser(null)
    }
  }, [])

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    canPublishNews: Boolean(user && (user.is_verified_author || user.is_admin)),
    isAdmin: Boolean(user && user.is_admin),
    login,
    register,
    logout,
    reloadUser: loadCurrentUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return ctx
}
