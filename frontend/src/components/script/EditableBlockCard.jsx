import { useState, useEffect } from 'react'
import { Edit2, Search, Check, X, ChevronDown, ChevronUp, Loader2, Image, Video } from 'lucide-react'
import KeywordEditor from './KeywordEditor'
import { blockApi } from '../../services/api'

/**
 * 편집 가능한 블록 카드 컴포넌트
 * @param {Object} block - 블록 데이터
 * @param {boolean} isSelected - 선택 여부
 * @param {function} onSelect - 선택 토글 콜백
 * @param {function} onUpdate - 블록 업데이트 콜백
 * @param {function} onBlockChange - 블록 변경 시 부모에 알림 (매칭 완료 등)
 */
function EditableBlockCard({ block, isSelected, onSelect, onUpdate, onBlockChange }) {
  const [isEditing, setIsEditing] = useState(false)
  const [isExpanded, setIsExpanded] = useState(true)
  const [text, setText] = useState(block.text)
  const [keywords, setKeywords] = useState(block.keywords || [])
  const [isSaving, setIsSaving] = useState(false)
  const [assets, setAssets] = useState([])
  const [isLoadingAssets, setIsLoadingAssets] = useState(false)
  const [isSearching, setIsSearching] = useState(false)

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
          setAssets(data.slice(0, 4)) // 최대 4개만 미리보기
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
      alert('키워드가 없습니다. 먼저 키워드를 추가해주세요.')
      return
    }

    setIsSearching(true)
    try {
      await blockApi.match(block.id, { video_priority: true })
      // 에셋 다시 로드
      const { data } = await blockApi.getAssets(block.id)
      setAssets(data.slice(0, 4))
      // 부모에 변경 알림
      if (onBlockChange) onBlockChange()
    } catch (err) {
      console.error('Failed to search assets:', err)
      alert(err.response?.data?.detail?.message || '에셋 검색에 실패했습니다.')
    } finally {
      setIsSearching(false)
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
            <p className="text-xs text-gray-500 mb-1.5">Keywords</p>
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
                <div className="grid grid-cols-4 gap-2">
                  {assets.map((item) => {
                    const asset = item.asset || item
                    return (
                      <div
                        key={item.id}
                        className={`relative aspect-video bg-dark-bg rounded overflow-hidden ${
                          item.is_primary ? 'ring-2 ring-primary' : ''
                        }`}
                      >
                        <img
                          src={asset.thumbnail_url}
                          alt={asset.title || 'Thumbnail'}
                          className="w-full h-full object-cover"
                        />
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
              ) : (
                <p className="text-xs text-gray-500">
                  No visuals yet. Click search to find.
                </p>
              )}
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
    </div>
  )
}

export default EditableBlockCard
