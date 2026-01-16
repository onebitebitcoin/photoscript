import { useState, useEffect } from 'react'
import { Edit2, Search, Check, X, ChevronDown, ChevronUp, Loader2, Image, Video, Play, Eye, Wand2, Trash2, Sparkles } from 'lucide-react'
import KeywordEditor from './KeywordEditor'
import { blockApi } from '../../services/api'
import toast from 'react-hot-toast'

/**
 * 편집 가능한 블록 카드 컴포넌트
 * @param {Object} block - 블록 데이터
 * @param {boolean} isSelected - 선택 여부
 * @param {boolean} isNew - 새로 추가된 블록 여부 (자동 편집 모드)
 * @param {function} onSelect - 선택 토글 콜백
 * @param {function} onUpdate - 블록 업데이트 콜백
 * @param {function} onBlockChange - 블록 변경 시 부모에 알림 (매칭 완료 등)
 * @param {function} onNewBlockProcessed - 새 블록 처리 완료 시 콜백
 * @param {function} onDelete - 블록 삭제 콜백
 */
function EditableBlockCard({ block, isSelected, isNew, onSelect, onUpdate, onBlockChange, onNewBlockProcessed, onDelete }) {
  const [isEditing, setIsEditing] = useState(false)
  const [isExpanded, setIsExpanded] = useState(true)
  const [text, setText] = useState(block.text)
  const [keywords, setKeywords] = useState(block.keywords || [])
  const [isSaving, setIsSaving] = useState(false)
  const [assets, setAssets] = useState([])
  const [isLoadingAssets, setIsLoadingAssets] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [modalAsset, setModalAsset] = useState(null) // 모달에 표시할 에셋
  const [searchKeyword, setSearchKeyword] = useState('') // 키워드 검색용
  const [isKeywordSearching, setIsKeywordSearching] = useState(false)
  const [selectingAssetId, setSelectingAssetId] = useState(null) // 선택 중인 에셋
  const [showCount, setShowCount] = useState(4) // 표시할 에셋 개수
  const [isExtractingKeywords, setIsExtractingKeywords] = useState(false) // 키워드 추출 중
  const [aiMode, setAiMode] = useState('link') // AI 모드: 'link' | 'enhance' | 'search'
  const [aiPrompt, setAiPrompt] = useState('') // AI 프롬프트 입력 (URL 또는 검색어)
  const [aiGuide, setAiGuide] = useState('') // AI 가이드 입력 (강화/반박 등)
  const [isGeneratingText, setIsGeneratingText] = useState(false) // 텍스트 생성 중

  // 새 블록인 경우 자동으로 편집 모드 진입
  useEffect(() => {
    if (isNew) {
      setIsEditing(true)
      onNewBlockProcessed?.()
    }
  }, [isNew, onNewBlockProcessed])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await onUpdate(block.id, { text, keywords })
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save block:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    setText(block.text)
    setKeywords(block.keywords || [])
    setIsEditing(false)
  }

  // 에셋 로드 (이미 매칭된 경우)
  useEffect(() => {
    const loadAssets = async () => {
      if (block.status === 'MATCHED' || block.status === 'CUSTOM') {
        setIsLoadingAssets(true)
        try {
          const { data } = await blockApi.getAssets(block.id)
          setAssets(data) // 전체 저장
          setShowCount(4) // 초기 표시 개수 리셋
        } catch (err) {
          console.error('Failed to load assets:', err)
        } finally {
          setIsLoadingAssets(false)
        }
      } else {
        setAssets([])
      }
    }
    loadAssets()
  }, [block.id, block.status])

  // 개별 블록 에셋 검색
  const handleSearch = async () => {
    if (!block.keywords?.length) {
      toast.error('키워드가 없습니다. 먼저 키워드를 추가해주세요.')
      return
    }

    setIsSearching(true)
    try {
      await blockApi.match(block.id, { video_priority: true })
      // 에셋 다시 로드 (로컬 상태만 업데이트)
      const { data } = await blockApi.getAssets(block.id)
      setAssets(data)
      setShowCount(4)
      toast.success(`${data.length}개 에셋 찾음`)
    } catch (err) {
      console.error('Failed to search assets:', err)
      toast.error(err.response?.data?.detail?.message || '에셋 검색에 실패했습니다.')
    } finally {
      setIsSearching(false)
    }
  }

  // 에셋 선택 (primary 설정)
  const handleSelectAsset = async (assetId) => {
    setSelectingAssetId(assetId)
    try {
      await blockApi.setPrimary(block.id, assetId)
      // 로컬 상태만 업데이트 (페이지 새로고침 없이)
      setAssets(prev => prev.map(a => ({
        ...a,
        is_primary: a.asset_id === assetId
      })))
      toast.success('Selected')
    } catch (err) {
      console.error('Failed to select asset:', err)
      toast.error('Failed to select')
    } finally {
      setSelectingAssetId(null)
    }
  }

  // 키워드로 추가 에셋 검색
  const handleKeywordSearch = async () => {
    if (!searchKeyword.trim()) {
      toast.error('키워드를 입력해주세요')
      return
    }

    setIsKeywordSearching(true)
    try {
      const { data: newAssets } = await blockApi.search(block.id, searchKeyword.trim(), { video_priority: true })
      if (newAssets.length > 0) {
        // 새 에셋으로 교체
        setAssets(newAssets)
        setShowCount(4)
        toast.success(`${newAssets.length}개 에셋 찾음`)
      } else {
        toast.error('검색 결과가 없습니다')
      }
      setSearchKeyword('')
    } catch (err) {
      console.error('Failed to search:', err)
      toast.error(err.response?.data?.detail?.message || '검색에 실패했습니다')
    } finally {
      setIsKeywordSearching(false)
    }
  }

  // 텍스트에서 키워드 자동 추출 (LLM)
  const handleExtractKeywords = async () => {
    if (!text.trim()) {
      toast.error('텍스트를 먼저 입력해주세요')
      return
    }

    setIsExtractingKeywords(true)
    try {
      // 먼저 텍스트를 저장
      await onUpdate(block.id, { text })

      // 키워드 추출
      const { data: updatedBlock } = await blockApi.extractKeywords(block.id)
      setKeywords(updatedBlock.keywords || [])
      toast.success(`${updatedBlock.keywords?.length || 0}개 키워드 추출됨`)
    } catch (err) {
      console.error('Failed to extract keywords:', err)
      toast.error(err.response?.data?.detail?.message || '키워드 추출에 실패했습니다')
    } finally {
      setIsExtractingKeywords(false)
    }
  }

  // 입력 검증
  const isValidInput = () => {
    if (aiMode === 'link') {
      return aiPrompt.trim().startsWith('http')
    } else if (aiMode === 'enhance') {
      return aiGuide.trim().length > 0
    } else if (aiMode === 'search') {
      return aiPrompt.trim().length > 0
    }
    return false
  }

  // AI로 텍스트 자동 생성
  const handleGenerateText = async () => {
    if (!isValidInput()) {
      const errorMsg =
        aiMode === 'link' ? 'URL을 입력해주세요' :
        aiMode === 'enhance' ? '가이드를 입력해주세요' :
        '검색어를 입력해주세요'
      toast.error(errorMsg)
      return
    }

    setIsGeneratingText(true)
    try {
      const { data: updatedBlock } = await blockApi.generateText(block.id, {
        mode: aiMode,
        prompt: aiMode === 'enhance' ? aiGuide : aiPrompt,
        user_guide: aiMode === 'enhance' ? null : (aiGuide || null)
      })
      setText(updatedBlock.text)
      setAiPrompt('')
      setAiGuide('')
      toast.success('텍스트가 생성되었습니다')
    } catch (err) {
      console.error('Failed to generate text:', err)
      toast.error(err.response?.data?.detail?.message || '텍스트 생성에 실패했습니다')
    } finally {
      setIsGeneratingText(false)
    }
  }

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
            BLOCK {block.index + 1}
          </span>
          <span className={`
            text-xs px-1.5 py-0.5 rounded
            ${block.status === 'DRAFT' ? 'bg-yellow-500/20 text-yellow-400' : ''}
            ${block.status === 'MATCHED' ? 'bg-green-500/20 text-green-400' : ''}
            ${block.status === 'NO_RESULT' ? 'bg-red-500/20 text-red-400' : ''}
            ${block.status === 'PENDING' ? 'bg-blue-500/20 text-blue-400' : ''}
          `}>
            {block.status}
          </span>
        </div>

        <div className="flex items-center gap-1">
          {!isEditing && (
            <>
              <button
                onClick={() => setIsEditing(true)}
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
            <div className="space-y-2 bg-dark-bg border border-dark-border rounded-md p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-400">AI 텍스트 생성</span>
              </div>

              {/* 모드 선택 - 라디오 버튼 */}
              <div className="flex gap-2">
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="radio"
                    name="aiMode"
                    value="link"
                    checked={aiMode === 'link'}
                    onChange={(e) => setAiMode(e.target.value)}
                    className="w-3 h-3 text-primary focus:ring-primary"
                  />
                  <span className="text-xs text-gray-300">링크</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="radio"
                    name="aiMode"
                    value="enhance"
                    checked={aiMode === 'enhance'}
                    onChange={(e) => setAiMode(e.target.value)}
                    className="w-3 h-3 text-primary focus:ring-primary"
                  />
                  <span className="text-xs text-gray-300">보완</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="radio"
                    name="aiMode"
                    value="search"
                    checked={aiMode === 'search'}
                    onChange={(e) => setAiMode(e.target.value)}
                    className="w-3 h-3 text-primary focus:ring-primary"
                  />
                  <span className="text-xs text-gray-300">검색</span>
                </label>
              </div>

              {/* 프롬프트 입력 (링크/검색 모드) */}
              {(aiMode === 'link' || aiMode === 'search') && (
                <input
                  type="text"
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  placeholder={aiMode === 'link' ? 'URL 입력...' : '검색어 입력...'}
                  className="w-full bg-dark-bg border border-dark-border rounded px-2 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                />
              )}

              {/* 가이드 입력 (모든 모드에서 선택적, 보완 모드는 필수) */}
              <textarea
                value={aiGuide}
                onChange={(e) => setAiGuide(e.target.value)}
                placeholder={
                  aiMode === 'enhance'
                    ? '가이드 입력 (예: 위 블록 강화, 반박 근거 추가...)'
                    : '추가 가이드 (선택사항)'
                }
                className="w-full bg-dark-bg border border-dark-border rounded px-2 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary resize-none"
                rows={2}
              />

              {/* 생성 버튼 */}
              <button
                onClick={handleGenerateText}
                disabled={isGeneratingText || !isValidInput()}
                className="w-full px-3 py-1.5 bg-primary/20 hover:bg-primary/30 rounded text-xs text-primary hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1"
              >
                {isGeneratingText ? (
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
          )}

          {/* 텍스트 */}
          {isEditing ? (
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="w-full bg-dark-bg border border-dark-border rounded-md p-2 text-sm text-white resize-none focus:outline-none focus:border-primary"
              rows={Math.min(10, Math.max(3, text.split('\n').length + 1))}
            />
          ) : (
            <p className="text-sm text-gray-200 whitespace-pre-wrap line-clamp-6">
              {block.text}
            </p>
          )}

          {/* 키워드 */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-xs text-gray-500">Keywords</p>
              {isEditing && (
                <button
                  onClick={handleExtractKeywords}
                  disabled={isExtractingKeywords || !text.trim()}
                  className="flex items-center gap-1 px-2 py-0.5 text-xs text-primary hover:text-primary-hover disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
                  title="텍스트에서 키워드 자동 추출"
                >
                  {isExtractingKeywords ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Wand2 className="w-3 h-3" />
                  )}
                  <span>Auto</span>
                </button>
              )}
            </div>
            <KeywordEditor
              keywords={isEditing ? keywords : (block.keywords || [])}
              onChange={setKeywords}
              editable={isEditing}
              maxKeywords={10}
            />
          </div>

          {/* 에셋 미리보기 */}
          {!isEditing && (
            <div>
              <p className="text-xs text-gray-500 mb-1.5">Visuals</p>
              {isLoadingAssets ? (
                <div className="flex items-center gap-2 text-gray-500 text-xs">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Loading...</span>
                </div>
              ) : assets.length > 0 ? (
                <>
                  <div className="grid grid-cols-4 gap-2">
                    {assets.slice(0, showCount).map((item) => {
                      const asset = item.asset || item
                      const hasPrimary = assets.some(a => a.is_primary)
                      const isDimmed = hasPrimary && !item.is_primary
                      const isSelecting = selectingAssetId === item.asset_id
                      return (
                        <div
                          key={item.id}
                          className={`relative aspect-video bg-dark-bg rounded overflow-hidden group transition-all ${
                            item.is_primary ? 'ring-2 ring-primary' : ''
                          } ${isDimmed ? 'opacity-40 hover:opacity-100' : ''}`}
                        >
                          <img
                            src={asset.thumbnail_url}
                            alt={asset.title || 'Thumbnail'}
                            className="w-full h-full object-cover"
                          />
                          {/* 호버 시 버튼 오버레이 */}
                          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
                            {/* 선택 버튼 */}
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleSelectAsset(item.asset_id)
                              }}
                              disabled={isSelecting || item.is_primary}
                              className={`p-1.5 rounded transition-colors ${
                                item.is_primary
                                  ? 'bg-primary text-white'
                                  : 'bg-white/20 hover:bg-primary text-white'
                              } disabled:opacity-50`}
                              title={item.is_primary ? 'Selected' : 'Use this'}
                            >
                              {isSelecting ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <Check className="w-3 h-3" />
                              )}
                            </button>
                            {/* 보기 버튼 */}
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                setModalAsset(asset)
                              }}
                              className="p-1.5 bg-white/20 hover:bg-white/40 rounded transition-colors text-white"
                              title="View"
                            >
                              {asset.asset_type === 'VIDEO' ? (
                                <Play className="w-3 h-3" />
                              ) : (
                                <Eye className="w-3 h-3" />
                              )}
                            </button>
                          </div>
                          {/* 타입 배지 */}
                          <span className={`absolute top-0.5 right-0.5 p-0.5 rounded ${
                            asset.asset_type === 'VIDEO' ? 'bg-blue-500' : 'bg-green-500'
                          }`}>
                            {asset.asset_type === 'VIDEO' ? (
                              <Video className="w-2.5 h-2.5 text-white" />
                            ) : (
                              <Image className="w-2.5 h-2.5 text-white" />
                            )}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                  {/* 더보기 버튼 */}
                  {assets.length > showCount && (
                    <button
                      onClick={() => setShowCount(prev => prev + 4)}
                      className="w-full mt-2 py-1.5 text-xs text-gray-400 hover:text-white bg-dark-hover hover:bg-dark-border rounded transition-colors"
                    >
                      More ({assets.length - showCount} left)
                    </button>
                  )}
                </>
              ) : (
                <p className="text-xs text-gray-500">
                  No visuals yet. Click search to find.
                </p>
              )}

              {/* 키워드 검색 */}
              <div className="flex gap-2 mt-2">
                <input
                  type="text"
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleKeywordSearch()}
                  placeholder="Search more..."
                  className="flex-1 bg-dark-bg border border-dark-border rounded px-2 py-1 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary"
                />
                <button
                  onClick={handleKeywordSearch}
                  disabled={isKeywordSearching}
                  className="px-2 py-1 bg-dark-hover hover:bg-primary/20 rounded text-xs text-gray-400 hover:text-white transition-colors disabled:opacity-50"
                >
                  {isKeywordSearching ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Search className="w-3 h-3" />
                  )}
                </button>
              </div>
            </div>
          )}

          {/* 편집 모드 버튼 */}
          {isEditing && (
            <div className="flex justify-end gap-2 pt-2 border-t border-dark-border">
              <button
                onClick={handleCancel}
                className="px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4 inline mr-1" />
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="px-3 py-1.5 text-sm bg-primary hover:bg-primary-hover text-white rounded-md transition-colors disabled:opacity-50"
              >
                <Check className="w-4 h-4 inline mr-1" />
                {isSaving ? 'Saving...' : 'Save'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* 미디어 모달 */}
      {modalAsset && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
          onClick={() => setModalAsset(null)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 닫기 버튼 */}
            <button
              onClick={() => setModalAsset(null)}
              className="absolute -top-10 right-0 p-2 text-white hover:text-gray-300 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>

            {/* 미디어 콘텐츠 */}
            <div className="bg-dark-card rounded-lg overflow-hidden">
              {modalAsset.asset_type === 'VIDEO' ? (
                <video
                  src={modalAsset.source_url}
                  poster={modalAsset.thumbnail_url}
                  controls
                  autoPlay
                  className="w-full max-h-[70vh] object-contain"
                />
              ) : (
                <img
                  src={modalAsset.source_url}
                  alt={modalAsset.title || 'Image'}
                  className="w-full max-h-[70vh] object-contain"
                />
              )}

              {/* 정보 */}
              <div className="p-3 border-t border-dark-border">
                <div className="flex items-center justify-between">
                  <div>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      modalAsset.asset_type === 'VIDEO' ? 'bg-blue-500' : 'bg-green-500'
                    } text-white`}>
                      {modalAsset.asset_type}
                    </span>
                    <span className="text-xs text-gray-400 ml-2 capitalize">
                      {modalAsset.provider}
                    </span>
                  </div>
                  <a
                    href={modalAsset.source_url}
                    download
                    className="text-xs text-primary hover:underline"
                  >
                    Download
                  </a>
                </div>
                {modalAsset.title && (
                  <p className="text-sm text-white mt-2">{modalAsset.title}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default EditableBlockCard
