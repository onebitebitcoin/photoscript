import { memo, useMemo } from 'react'
import { Loader2, Sparkles, Link, Globe, MessageSquare } from 'lucide-react'
import { detectMode } from '../../utils/detectMode'
import { getModeBadgeClass } from '../../constants/styles'

/**
 * AI 텍스트 생성 컴포넌트
 * @param {string} prompt - AI 프롬프트
 * @param {function} onPromptChange - 프롬프트 변경 콜백
 * @param {function} onGenerate - 생성 실행 콜백
 * @param {boolean} isGenerating - 생성 중 여부
 */
function AITextGenerator({ prompt, onPromptChange, onGenerate, isGenerating }) {
  // 실시간 모드 감지
  const detectedMode = useMemo(() => detectMode(prompt), [prompt])

  const ModeIcon = {
    link: Link,
    search: Globe,
    enhance: MessageSquare,
  }[detectedMode.mode]

  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      if (prompt.trim() && !isGenerating) {
        onGenerate()
      }
    }
  }

  return (
    <div className="space-y-2 bg-dark-bg border border-dark-border rounded-md p-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-gray-400">AI 텍스트 생성</span>
        {/* 실시간 모드 표시 */}
        {prompt.trim() && (
          <span className={`text-xs px-2 py-0.5 rounded flex items-center gap-1 ${getModeBadgeClass(detectedMode.mode)}`}>
            <ModeIcon className="w-3 h-3" />
            <span>{detectedMode.label}</span>
          </span>
        )}
      </div>

      {/* 단일 프롬프트 입력 */}
      <textarea
        value={prompt}
        onChange={(e) => onPromptChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="URL, '검색해서' 포함 검색어, 또는 직접 지시... (Cmd+Enter로 생성)"
        className="w-full bg-dark-bg border border-dark-border rounded px-2 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary resize-none"
        rows={2}
      />

      {/* 모드 힌트 */}
      <p className="text-xs text-gray-500">
        {detectedMode.description}
      </p>

      {/* 생성 버튼 */}
      <button
        onClick={onGenerate}
        disabled={isGenerating || !prompt.trim()}
        className="w-full px-3 py-1.5 bg-primary/20 hover:bg-primary/30 rounded text-xs text-primary hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1"
      >
        {isGenerating ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>생성 중...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI 텍스트 생성</span>
          </>
        )}
      </button>
    </div>
  )
}

export default memo(AITextGenerator)
