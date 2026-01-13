import { AlertCircle, X } from 'lucide-react'

/**
 * 에러 알림 컴포넌트
 */
function ErrorAlert({ error, onClose }) {
  if (!error) return null

  const message = typeof error === 'string' ? error : error.message || 'An error occurred'
  const details = error?.details || error?.response?.data?.detail?.message

  return (
    <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-red-400 font-medium">{message}</p>
          {details && (
            <p className="text-red-400/70 text-sm mt-1">{details}</p>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-red-400/70 hover:text-red-400 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}

export default ErrorAlert
