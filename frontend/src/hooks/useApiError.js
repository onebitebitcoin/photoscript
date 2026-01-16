import toast from 'react-hot-toast'
import logger from '../utils/logger'

/**
 * API 에러 처리 통합 훅
 * - 에러 메시지 추출
 * - logger.error 로깅
 * - toast.error 알림
 */
export function useApiError() {
  /**
   * 에러 객체에서 사용자 친화적 메시지 추출
   * @param {Error} err - 에러 객체
   * @param {string} fallback - 기본 메시지
   * @returns {string} 에러 메시지
   */
  const getErrorMessage = (err, fallback = '오류가 발생했습니다') => {
    return err.response?.data?.detail?.message || err.message || fallback
  }

  /**
   * 에러 처리 (로깅 + 토스트)
   * @param {Error} err - 에러 객체
   * @param {string} context - 에러 발생 컨텍스트 (예: 'Failed to save block')
   * @returns {string} 에러 메시지
   */
  const handleError = (err, context) => {
    const message = getErrorMessage(err, `${context} 실패`)
    logger.error(context, { error: err.message, stack: err.stack })
    toast.error(message)
    return message
  }

  return { getErrorMessage, handleError }
}

export default useApiError
