import { memo, useState } from 'react'
import { Copy, FileCheck, Loader2, History } from 'lucide-react'
import { renderTextWithLinks } from './EditableBlockCard'
import { projectApi } from '../../services/api'
import QAResultView from './QAResultView'
import toast from 'react-hot-toast'
import logger from '../../utils/logger'

/**
 * 통합 문서 보기 컴포넌트
 * 모든 블록을 하나의 문서로 합쳐서 표시 (읽기 전용)
 * 복사 기능 및 QA 검증 기능 포함
 */
function UnifiedDocumentView({ blocks, projectId }) {
  const [isCopying, setIsCopying] = useState(false)
  const [isQALoading, setIsQALoading] = useState(false)
  const [viewMode, setViewMode] = useState('script') // 'script' | 'qa' | 'versions'
  const [qaResult, setQaResult] = useState(null)
  const [additionalPrompt, setAdditionalPrompt] = useState('')
  const [qaProgress, setQaProgress] = useState(0)
  const [qaStatus, setQaStatus] = useState('')

  // 복사 핸들러
  const handleCopy = async () => {
    try {
      setIsCopying(true)
      const fullScript = blocks.map(b => b.text).join('\n\n')
      await navigator.clipboard.writeText(fullScript)
      toast.success('스크립트가 클립보드에 복사되었습니다')
      logger.info('Script copied to clipboard')
    } catch (err) {
      toast.error('복사 실패')
      logger.error('Failed to copy script', { error: err.message })
    } finally {
      setIsCopying(false)
    }
  }

  // QA 검증 핸들러 (비동기 패턴)
  const handleQA = async () => {
    try {
      setIsQALoading(true)
      setQaProgress(0)
      setQaStatus('작업 생성 중...')

      const options = additionalPrompt ? { additional_prompt: additionalPrompt } : {}

      // 1. QA 작업 생성 (즉시 반환)
      const { data: taskData } = await projectApi.qaScriptAsync(projectId, options)
      const taskId = taskData.id

      logger.info('QA task created', { taskId, projectId })
      setQaStatus('QA 검증 진행 중...')

      // 2. 폴링으로 상태 확인 (2초마다)
      const pollInterval = setInterval(async () => {
        try {
          const { data: statusData } = await projectApi.getQATaskStatus(projectId, taskId)

          setQaProgress(statusData.progress)

          if (statusData.status === 'completed') {
            clearInterval(pollInterval)
            setQaResult(statusData.result)
            setViewMode('qa')
            setIsQALoading(false)
            toast.success('QA 검증 완료 (버전 자동 저장됨)')
            logger.info('QA validation completed', { taskId, projectId })
          } else if (statusData.status === 'failed') {
            clearInterval(pollInterval)
            setIsQALoading(false)
            const errorMsg = statusData.error_message || '알 수 없는 오류'
            toast.error(`QA 검증 실패: ${errorMsg}`)
            logger.error('QA validation failed', { taskId, error: errorMsg })
          } else if (statusData.status === 'running') {
            setQaStatus(`QA 검증 진행 중... (${statusData.progress}%)`)
          }
        } catch (pollErr) {
          logger.error('Failed to poll QA status', { error: pollErr.message })
        }
      }, 2000)

      // 5분 후 타임아웃
      setTimeout(() => {
        clearInterval(pollInterval)
        if (isQALoading) {
          setIsQALoading(false)
          toast.error('QA 검증 시간 초과')
          logger.error('QA validation timeout', { taskId })
        }
      }, 300000) // 5분

    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      toast.error(`QA 검증 실패: ${message}`)
      logger.error('QA validation failed', { projectId, error: message })
      setIsQALoading(false)
    }
  }

  // 스크립트 보기로 돌아가기
  const handleBackToScript = () => {
    setViewMode('script')
  }

  // 이전 버전 보기
  const handleViewVersions = () => {
    setViewMode('versions')
    logger.info('Viewing QA versions', { projectId })
  }

  if (!blocks?.length) {
    return (
      <div className="max-w-3xl mx-auto px-4 md:px-6 py-12 text-center">
        <p className="text-gray-400">표시할 블록이 없습니다</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-2 md:px-6 py-6">
      {/* 상단 버튼 영역 */}
      <div className="mb-6 space-y-3">
        <div className="flex items-center gap-2 flex-wrap overflow-x-auto pb-1">
          {viewMode === 'script' ? (
            <>
              <button
                onClick={handleCopy}
                disabled={isCopying}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-dark-card border border-dark-border rounded-lg hover:bg-dark-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap flex-shrink-0"
              >
                {isCopying ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
                <span className="text-sm">복사</span>
              </button>
              <button
                onClick={handleQA}
                disabled={isQALoading}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-primary/10 border border-primary/30 text-primary rounded-lg hover:bg-primary/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap flex-shrink-0"
              >
                {isQALoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <FileCheck className="w-4 h-4" />
                )}
                <span className="text-sm">
                  {isQALoading ? `${qaStatus} ${qaProgress}%` : 'QA 검증'}
                </span>
              </button>
              <button
                onClick={handleViewVersions}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-dark-card border border-dark-border rounded-lg hover:bg-dark-hover transition-colors whitespace-nowrap flex-shrink-0"
              >
                <History className="w-4 h-4" />
                <span className="text-sm">이전 버전</span>
              </button>
            </>
          ) : (
            <button
              onClick={handleBackToScript}
              className="flex items-center gap-1.5 px-2.5 py-1.5 bg-dark-card border border-dark-border rounded-lg hover:bg-dark-hover transition-colors whitespace-nowrap"
            >
              <span className="text-sm">← 스크립트 보기</span>
            </button>
          )}
        </div>

        {/* 추가 프롬프트 입력란 (스크립트 모드에서만 표시) */}
        {viewMode === 'script' && (
          <div className="w-full">
            <textarea
              value={additionalPrompt}
              onChange={(e) => setAdditionalPrompt(e.target.value)}
              placeholder="추가 요구사항 (선택사항, 예: '더 격식있게', '전문 용어 쉽게')"
              rows={2}
              maxLength={2000}
              className="w-full px-3 py-2 bg-dark-card border border-dark-border rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
            />
            {additionalPrompt.length > 0 && (
              <div className="text-xs text-gray-500 text-right mt-1">
                {additionalPrompt.length} / 2000
              </div>
            )}
          </div>
        )}
      </div>

      {/* 콘텐츠 영역 */}
      {viewMode === 'script' ? (
        // 일반 스크립트 보기
        <div>
          {blocks.map((block, index) => (
            <div key={block.id} className={index < blocks.length - 1 ? 'mb-8' : ''}>
              <div className="text-gray-200 whitespace-pre-wrap">
                {renderTextWithLinks(block.text)}
              </div>
            </div>
          ))}
        </div>
      ) : viewMode === 'qa' ? (
        // QA 결과 보기
        <QAResultView qaResult={qaResult} projectId={projectId} />
      ) : (
        // 이전 버전 목록 보기
        <QAResultView qaResult={null} projectId={projectId} initialTab="versions" />
      )}
    </div>
  )
}

export default memo(UnifiedDocumentView)
