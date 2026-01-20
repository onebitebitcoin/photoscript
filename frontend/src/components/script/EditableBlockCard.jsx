import { useState, useEffect, memo, useCallback } from 'react'
import { Edit2, Search, ChevronDown, ChevronUp, Loader2, Trash2, Code, X } from 'lucide-react'
import { blockApi } from '../../services/api'
import toast from 'react-hot-toast'
import logger from '../../utils/logger'
import { useBlockAssets } from '../../hooks/useBlockAssets'
import { TOAST } from '../../constants/messages'
import { getStatusBadgeClass, getModeBadgeClass } from '../../constants/styles'

// 분리된 컴포넌트들
import AssetModal from '../common/AssetModal'
import AITextGenerator from './AITextGenerator'
import BlockTextEditor from './BlockTextEditor'
import BlockAssetSection from './BlockAssetSection'

/**
 * 텍스트에서 URL을 감지하여 클릭 가능한 링크로 변환
 */
export function renderTextWithLinks(text) {
  if (!text) return null

  const urlPattern = /(https?:\/\/[^\s]+)/g
  const parts = text.split(urlPattern)

  return parts.map((part, index) => {
    if (/^https?:\/\//.test(part)) {
      return (
        <a
          key={index}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:text-primary-hover underline break-all"
          onClick={(e) => e.stopPropagation()}
        >
          {part}
        </a>
      )
    }
    return <span key={index}>{part}</span>
  })
}

/**
 * 편집 가능한 블록 카드 컴포넌트
 */
function EditableBlockCard({
  block,
  index,
  isSelected,
  isNew,
  isEditing = false,
  onSelect,
  onUpdate,
  onNewBlockProcessed,
  onDelete,
  onEditStart,
  onEditEnd
}) {
  // 편집 상태는 부모로부터 전달받음
  const [isExpanded, setIsExpanded] = useState(true)
  const [text, setText] = useState(block.text)
  const [isSaving, setIsSaving] = useState(false)

  // AI 생성 상태
  const [aiPrompt, setAiPrompt] = useState('')
  const [isGeneratingText, setIsGeneratingText] = useState(false)
  const [generationInfo, setGenerationInfo] = useState(null) // 생성 정보
  const [showGenerationInfo, setShowGenerationInfo] = useState(false) // 생성 정보 표시 여부

  // 에셋 관련 상태
  const [isSearching, setIsSearching] = useState(false)
  const [modalAsset, setModalAsset] = useState(null)
  const [selectingAssetId, setSelectingAssetId] = useState(null)

  // 에셋 훅 사용
  const {
    assets,
    isLoading: isLoadingAssets,
    setPrimary,
    matchAssets,
    searchByKeyword
  } = useBlockAssets(block.id, block.status)

  // 새 블록인 경우 자동으로 편집 모드 진입
  useEffect(() => {
    if (isNew) {
      onEditStart?.(block.id)
      onNewBlockProcessed?.()
    }
  }, [isNew, onNewBlockProcessed, onEditStart, block.id])

  // 블록 저장
  const handleSave = useCallback(async () => {
    setIsSaving(true)
    try {
      await onUpdate(block.id, { text })
      onEditEnd?.(block.id)
      logger.info('Block saved', { blockId: block.id })
    } catch (error) {
      logger.error('Failed to save block', { blockId: block.id, error: error.message })
      toast.error(error.response?.data?.detail?.message || '저장에 실패했습니다')
    } finally {
      setIsSaving(false)
    }
  }, [block.id, text, onUpdate, onEditEnd])

  // 편집 취소
  const handleCancel = useCallback(() => {
    setText(block.text)
    onEditEnd?.(block.id)
  }, [block.text, onEditEnd, block.id])

  // 에셋 검색 (키워드 기반)
  const handleSearch = useCallback(async () => {
    if (!block.keywords?.length) {
      toast.error(TOAST.ERROR.NO_KEYWORD)
      return
    }

    setIsSearching(true)
    try {
      await matchAssets()
    } catch (err) {
      // 에러는 훅 내부에서 처리됨
    } finally {
      setIsSearching(false)
    }
  }, [block.keywords, matchAssets])

  // 에셋 선택 (primary 설정)
  const handleSelectAsset = useCallback(async (assetId) => {
    setSelectingAssetId(assetId)
    try {
      await setPrimary(assetId)
    } finally {
      setSelectingAssetId(null)
    }
  }, [setPrimary])

  // 키워드로 추가 에셋 검색
  const handleKeywordSearch = useCallback(async (keyword) => {
    try {
      await searchByKeyword(keyword)
    } catch (err) {
      // 에러는 훅 내부에서 처리됨
    }
  }, [searchByKeyword])

  // AI 텍스트 생성
  const handleGenerateText = useCallback(async () => {
    if (!aiPrompt.trim()) {
      toast.error(TOAST.ERROR.EMPTY_PROMPT)
      return
    }

    setIsGeneratingText(true)
    try {
      const { data: updatedBlock } = await blockApi.generateText(block.id, {
        prompt: aiPrompt
      })
      setText(updatedBlock.text)
      // 생성 정보 저장 (프롬프트는 유지)
      if (updatedBlock.generation_info) {
        setGenerationInfo(updatedBlock.generation_info)
      }
      toast.success(TOAST.SUCCESS.TEXT_GENERATED)
      logger.info('Text generated', { blockId: block.id, mode: updatedBlock.generation_info?.mode })
    } catch (err) {
      logger.error('Failed to generate text', { blockId: block.id, error: err.message })
      toast.error(err.response?.data?.detail?.message || TOAST.ERROR.TEXT_GENERATION_FAILED)
    } finally {
      setIsGeneratingText(false)
    }
  }, [block.id, aiPrompt])

  return (
    <div
      className={`
        bg-dark-card rounded-lg border transition-all
        ${isSelected ? 'border-primary ring-1 ring-primary' : 'border-dark-border'}
      `}
    >
      {/* 헤더 */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-dark-border">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onSelect(block.id)}
            className="w-4 h-4 rounded border-dark-border bg-dark-bg text-primary focus:ring-primary focus:ring-offset-0"
          />
          <span className="text-xs font-medium text-gray-400">
            BLOCK {index + 1}
          </span>
          <span className={`text-xs px-1.5 py-0.5 rounded ${getStatusBadgeClass(block.status)}`}>
            {block.status}
          </span>
        </div>

        <div className="flex items-center gap-1">
          {!isEditing && (
            <>
              <button
                onClick={() => onEditStart?.(block.id)}
                className="p-1.5 hover:bg-dark-hover rounded transition-colors"
                title="Edit"
              >
                <Edit2 className="w-4 h-4 text-gray-400" />
              </button>
              <button
                onClick={handleSearch}
                disabled={isSearching}
                className="p-1.5 hover:bg-dark-hover rounded transition-colors disabled:opacity-50"
                title="Search visuals"
              >
                {isSearching ? (
                  <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                ) : (
                  <Search className="w-4 h-4 text-gray-400" />
                )}
              </button>
              <button
                onClick={() => onDelete?.(block.id)}
                className="p-1.5 hover:bg-red-500/20 rounded transition-colors"
                title="Delete block"
              >
                <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-400" />
              </button>
            </>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 hover:bg-dark-hover rounded transition-colors"
          >
            {isExpanded
              ? <ChevronUp className="w-4 h-4 text-gray-400" />
              : <ChevronDown className="w-4 h-4 text-gray-400" />
            }
          </button>
        </div>
      </div>

      {/* 본문 */}
      {isExpanded && (
        <div className="p-3 space-y-3">
          {/* AI 텍스트 생성 (편집 모드에서만) */}
          {isEditing && (
            <AITextGenerator
              prompt={aiPrompt}
              onPromptChange={setAiPrompt}
              onGenerate={handleGenerateText}
              isGenerating={isGeneratingText}
            />
          )}

          {/* 텍스트 편집/표시 */}
          {isEditing ? (
            <BlockTextEditor
              text={text}
              onChange={setText}
              onSave={handleSave}
              onCancel={handleCancel}
              isSaving={isSaving}
            />
          ) : (
            <>
              <p className="text-sm text-gray-200 whitespace-pre-wrap">
                {renderTextWithLinks(block.text)}
              </p>

              {/* 생성 정보 토글 버튼 */}
              {generationInfo && (
                <button
                  onClick={() => setShowGenerationInfo(!showGenerationInfo)}
                  className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 mt-2 transition-colors"
                >
                  <Code className="w-3 h-3" />
                  <span>{showGenerationInfo ? '프롬프트 닫기' : '프롬프트 열기'}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] ${getModeBadgeClass(generationInfo.mode)}`}>
                    {generationInfo.mode}
                  </span>
                </button>
              )}

              {/* 생성 정보 표시 */}
              {showGenerationInfo && generationInfo && (
                <div className="mt-2 p-3 bg-dark-bg border border-dark-border rounded-md text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 font-medium">AI 생성 정보</span>
                    <button
                      onClick={() => setShowGenerationInfo(false)}
                      className="text-gray-500 hover:text-gray-300"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="space-y-1.5">
                    <div>
                      <span className="text-gray-500">Model: </span>
                      <span className="text-gray-300">{generationInfo.model}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Mode: </span>
                      <span className={`px-1.5 py-0.5 rounded ${getModeBadgeClass(generationInfo.mode)}`}>
                        {generationInfo.mode}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">User Prompt: </span>
                      <span className="text-gray-300 break-all">{generationInfo.user_prompt}</span>
                    </div>
                  </div>

                  <details className="mt-2">
                    <summary className="text-gray-500 cursor-pointer hover:text-gray-300">
                      System Prompt
                    </summary>
                    <pre className="mt-1 p-2 bg-dark-card rounded text-gray-400 whitespace-pre-wrap text-[10px] max-h-32 overflow-y-auto">
                      {generationInfo.system_prompt}
                    </pre>
                  </details>

                  <details className="mt-2">
                    <summary className="text-gray-500 cursor-pointer hover:text-gray-300">
                      Full Prompt (LLM에 전달된 전체 프롬프트)
                    </summary>
                    <pre className="mt-1 p-2 bg-dark-card rounded text-gray-400 whitespace-pre-wrap text-[10px] max-h-48 overflow-y-auto">
                      {generationInfo.full_prompt}
                    </pre>
                  </details>
                </div>
              )}
            </>
          )}

          {/* 에셋 섹션 (보기 모드에서만) */}
          {!isEditing && (
            <BlockAssetSection
              assets={assets}
              isLoading={isLoadingAssets}
              onSelectAsset={handleSelectAsset}
              onKeywordSearch={handleKeywordSearch}
              onViewAsset={setModalAsset}
              selectingAssetId={selectingAssetId}
            />
          )}
        </div>
      )}

      {/* 미디어 모달 */}
      <AssetModal
        asset={modalAsset}
        onClose={() => setModalAsset(null)}
      />
    </div>
  )
}

export default memo(EditableBlockCard)
