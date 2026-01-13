import { useState } from 'react'
import { Edit2, Scissors, Check, X, ChevronDown, ChevronUp } from 'lucide-react'
import KeywordEditor from './KeywordEditor'

/**
 * 편집 가능한 블록 카드 컴포넌트
 * @param {Object} block - 블록 데이터
 * @param {boolean} isSelected - 선택 여부
 * @param {function} onSelect - 선택 토글 콜백
 * @param {function} onUpdate - 블록 업데이트 콜백
 * @param {function} onSplit - 블록 나누기 콜백
 */
function EditableBlockCard({ block, isSelected, onSelect, onUpdate, onSplit }) {
  const [isEditing, setIsEditing] = useState(false)
  const [isExpanded, setIsExpanded] = useState(true)
  const [text, setText] = useState(block.text)
  const [keywords, setKeywords] = useState(block.keywords || [])
  const [isSaving, setIsSaving] = useState(false)

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

  const handleSplit = () => {
    // 중간 지점에서 나누기
    const midPoint = Math.floor(text.length / 2)
    // 가장 가까운 문장 끝이나 공백 찾기
    let splitPoint = midPoint
    const sentenceEnd = text.indexOf('.', midPoint)
    const newline = text.indexOf('\n', midPoint)

    if (sentenceEnd > 0 && sentenceEnd < midPoint + 100) {
      splitPoint = sentenceEnd + 1
    } else if (newline > 0 && newline < midPoint + 50) {
      splitPoint = newline + 1
    }

    onSplit(block.id, splitPoint)
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
                onClick={handleSplit}
                className="p-1.5 hover:bg-dark-hover rounded transition-colors"
                title="Split"
              >
                <Scissors className="w-4 h-4 text-gray-400" />
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
