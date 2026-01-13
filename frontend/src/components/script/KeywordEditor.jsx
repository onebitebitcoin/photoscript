import { useState } from 'react'
import { X, Plus } from 'lucide-react'

/**
 * 키워드 편집기 컴포넌트
 * @param {string[]} keywords - 키워드 목록
 * @param {function} onChange - 키워드 변경 시 콜백
 * @param {boolean} editable - 편집 가능 여부
 * @param {number} maxKeywords - 최대 키워드 수
 */
function KeywordEditor({ keywords = [], onChange, editable = false, maxKeywords = 10 }) {
  const [newKeyword, setNewKeyword] = useState('')

  const addKeyword = () => {
    const trimmed = newKeyword.trim()
    if (trimmed && !keywords.includes(trimmed) && keywords.length < maxKeywords) {
      onChange([...keywords, trimmed])
      setNewKeyword('')
    }
  }

  const removeKeyword = (kw) => {
    onChange(keywords.filter(k => k !== kw))
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addKeyword()
    }
  }

  return (
    <div className="space-y-2">
      {/* 키워드 태그 목록 */}
      <div className="flex flex-wrap gap-1.5">
        {keywords.map((kw, i) => (
          <span
            key={i}
            className={`
              text-xs px-2 py-1 rounded-md flex items-center gap-1
              ${editable
                ? 'bg-primary/20 text-primary border border-primary/30'
                : 'bg-dark-bg text-gray-400 border border-dark-border'
              }
            `}
          >
            {kw}
            {editable && (
              <button
                onClick={() => removeKeyword(kw)}
                className="hover:text-red-400 transition-colors"
                type="button"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </span>
        ))}
        {keywords.length === 0 && !editable && (
          <span className="text-xs text-gray-500">No keywords</span>
        )}
      </div>

      {/* 키워드 입력 (편집 모드) */}
      {editable && keywords.length < maxKeywords && (
        <div className="flex gap-2">
          <input
            type="text"
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Add keyword (English)"
            className="flex-1 bg-dark-bg border border-dark-border rounded-md px-2 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary"
          />
          <button
            onClick={addKeyword}
            disabled={!newKeyword.trim()}
            className="p-1.5 bg-dark-bg border border-dark-border rounded-md hover:bg-dark-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            type="button"
          >
            <Plus className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      )}

      {/* 최대 개수 안내 */}
      {editable && (
        <p className="text-xs text-gray-500">
          {keywords.length}/{maxKeywords} keywords
        </p>
      )}
    </div>
  )
}

export default KeywordEditor
