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
 * @param {string} message - 로딩 메시지
 * @param {function} onCancel - 취소 버튼 클릭 핸들러 (없으면 취소 버튼 숨김)
 */
export function LoadingOverlay({ message = 'Loading...', onCancel }) {
  return (
    <div className="fixed inset-0 bg-dark-bg/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-dark-card border border-dark-border rounded-lg p-6 flex flex-col items-center gap-4">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
        <p className="text-white">{message}</p>
        {onCancel && (
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white border border-dark-border rounded-lg hover:bg-dark-bg transition-colors"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}

export default Loading
