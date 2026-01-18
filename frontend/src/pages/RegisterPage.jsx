import { useState, useEffect, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Loader2, Check, X } from 'lucide-react'
import toast from 'react-hot-toast'

import { useAuth } from '../contexts/AuthContext'
import logger from '../utils/logger'

function RegisterPage() {
  const navigate = useNavigate()
  const { register, checkNickname } = useAuth()

  const [nickname, setNickname] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [nicknameStatus, setNicknameStatus] = useState(null) // null | 'checking' | 'available' | 'taken'
  const [nicknameMessage, setNicknameMessage] = useState('')

  // 닉네임 중복체크 (디바운스)
  const checkNicknameDebounced = useCallback(async (value) => {
    if (value.length < 2) {
      setNicknameStatus(null)
      setNicknameMessage('')
      return
    }

    setNicknameStatus('checking')
    try {
      const result = await checkNickname(value)
      setNicknameStatus(result.available ? 'available' : 'taken')
      setNicknameMessage(result.message)
    } catch (err) {
      logger.error('Nickname check failed', err)
      setNicknameStatus(null)
      setNicknameMessage('')
    }
  }, [checkNickname])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (nickname.trim()) {
        checkNicknameDebounced(nickname.trim())
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [nickname, checkNicknameDebounced])

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!nickname.trim() || !password.trim()) {
      toast.error('닉네임과 비밀번호를 입력해주세요')
      return
    }

    if (nickname.length < 2) {
      toast.error('닉네임은 2자 이상이어야 합니다')
      return
    }

    if (password.length < 4) {
      toast.error('비밀번호는 4자 이상이어야 합니다')
      return
    }

    if (password !== passwordConfirm) {
      toast.error('비밀번호가 일치하지 않습니다')
      return
    }

    if (nicknameStatus !== 'available') {
      toast.error('닉네임 중복확인을 해주세요')
      return
    }

    setIsLoading(true)
    try {
      await register(nickname, password)
      toast.success('회원가입 성공')
      navigate('/')
    } catch (err) {
      logger.error('Register failed', err)
      const message = err.response?.data?.detail?.message || '회원가입에 실패했습니다'
      toast.error(message)
    } finally {
      setIsLoading(false)
    }
  }

  const renderNicknameStatus = () => {
    if (!nickname || nickname.length < 2) return null

    switch (nicknameStatus) {
      case 'checking':
        return <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
      case 'available':
        return <Check className="w-4 h-4 text-green-500" />
      case 'taken':
        return <X className="w-4 h-4 text-red-500" />
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold text-white text-center mb-8">회원가입</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <div className="relative">
              <input
                type="text"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="닉네임 (2자 이상)"
                disabled={isLoading}
                className="w-full bg-dark-card border border-dark-border rounded-lg px-4 py-3 pr-10 text-white placeholder-gray-500 outline-none focus:border-primary disabled:opacity-50"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                {renderNicknameStatus()}
              </div>
            </div>
            {nicknameMessage && (
              <p className={`text-sm mt-1 ${nicknameStatus === 'available' ? 'text-green-500' : 'text-red-500'}`}>
                {nicknameMessage}
              </p>
            )}
          </div>

          <div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호 (4자 이상)"
              disabled={isLoading}
              className="w-full bg-dark-card border border-dark-border rounded-lg px-4 py-3 text-white placeholder-gray-500 outline-none focus:border-primary disabled:opacity-50"
            />
          </div>

          <div>
            <input
              type="password"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              placeholder="비밀번호 확인"
              disabled={isLoading}
              className="w-full bg-dark-card border border-dark-border rounded-lg px-4 py-3 text-white placeholder-gray-500 outline-none focus:border-primary disabled:opacity-50"
            />
            {passwordConfirm && password !== passwordConfirm && (
              <p className="text-sm mt-1 text-red-500">비밀번호가 일치하지 않습니다</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading || nicknameStatus !== 'available'}
            className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            회원가입
          </button>
        </form>

        <p className="text-center text-gray-500 mt-6">
          이미 계정이 있으신가요?{' '}
          <Link to="/login" className="text-primary hover:underline">
            로그인
          </Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage
