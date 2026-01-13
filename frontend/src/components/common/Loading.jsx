import { Loader2 } from 'lucide-react'

/**
 * 로딩 컴포넌트
 * @param {string} size - 'sm' | 'md' | 'lg'
 * @param {string} message - 로딩 메시지
 */
function Loading({ size = 'md', message = '' }) {
  const sizeStyles = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }

  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8">
      <Loader2 className={`${sizeStyles[size]} text-primary animate-spin`} />
      {message && (
        <p className="text-sm text-gray-400">{message}</p>
      )}
    </div>
  )
}

/**
 * 전체 화면 로딩 오버레이
 */
export function LoadingOverlay({ message = 'Loading...' }) {
  return (
    <div className="fixed inset-0 bg-dark-bg/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-dark-card border border-dark-border rounded-lg p-6 flex flex-col items-center gap-4">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
        <p className="text-white">{message}</p>
      </div>
    </div>
  )
}

export default Loading
