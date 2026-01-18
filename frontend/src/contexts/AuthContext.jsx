/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authApi, getStoredToken, setStoredToken, removeStoredToken } from '../services/api'
import logger from '../utils/logger'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  // 초기 로드 시 토큰 검증
  useEffect(() => {
    const validateToken = async () => {
      const token = getStoredToken()
      if (!token) {
        setIsLoading(false)
        return
      }

      try {
        const { data } = await authApi.getMe()
        setUser(data)
        logger.info('Token validated', { nickname: data.nickname })
      } catch (err) {
        logger.error('Token validation failed', err)
        removeStoredToken()
      } finally {
        setIsLoading(false)
      }
    }

    validateToken()
  }, [])

  // 로그인
  const login = useCallback(async (nickname, password) => {
    const { data } = await authApi.login({ nickname, password })
    setStoredToken(data.access_token)
    setUser(data.user)
    logger.info('User logged in', { nickname: data.user.nickname })
    return data.user
  }, [])

  // 회원가입
  const register = useCallback(async (nickname, password) => {
    const { data } = await authApi.register({ nickname, password })
    setStoredToken(data.access_token)
    setUser(data.user)
    logger.info('User registered', { nickname: data.user.nickname })
    return data.user
  }, [])

  // 로그아웃
  const logout = useCallback(() => {
    removeStoredToken()
    setUser(null)
    logger.info('User logged out')
  }, [])

  // 닉네임 중복체크
  const checkNickname = useCallback(async (nickname) => {
    const { data } = await authApi.checkNickname(nickname)
    return data
  }, [])

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    checkNickname,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
