import { Bold, Italic, List, Wand2 } from 'lucide-react'

/**
 * 스크립트 편집기 컴포넌트
 */
function ScriptEditor({ value, onChange, disabled = false, placeholder = '' }) {
  const wordCount = value ? value.trim().split(/\s+/).filter(Boolean).length : 0
  const charCount = value ? value.length : 0

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg overflow-hidden">
      {/* 툴바 */}
      <div className="flex items-center gap-1 px-3 py-2 border-b border-dark-border bg-dark-bg/50">
        <button
          type="button"
          className="p-1.5 text-gray-400 hover:text-white hover:bg-dark-hover rounded"
          title="Bold"
        >
          <Bold className="w-4 h-4" />
        </button>
        <button
          type="button"
          className="p-1.5 text-gray-400 hover:text-white hover:bg-dark-hover rounded"
          title="Italic"
        >
          <Italic className="w-4 h-4" />
        </button>
        <button
          type="button"
          className="p-1.5 text-gray-400 hover:text-white hover:bg-dark-hover rounded"
          title="List"
        >
          <List className="w-4 h-4" />
        </button>
        <button
          type="button"
          className="p-1.5 text-gray-400 hover:text-white hover:bg-dark-hover rounded"
          title="AI Assist"
        >
          <Wand2 className="w-4 h-4" />
        </button>

        <span className="ml-auto text-xs text-gray-500">Auto-saving...</span>
      </div>

      {/* 텍스트 영역 */}
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="w-full h-64 md:h-80 lg:h-96 p-4 bg-transparent text-white placeholder-gray-500 resize-none outline-none"
        style={{ minHeight: '300px' }}
      />

      {/* 하단 정보 */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-dark-border bg-dark-bg/50 text-xs text-gray-500">
        <span>Words: {wordCount}</span>
        <span>Characters: {charCount.toLocaleString()}</span>
      </div>
    </div>
  )
}

export default ScriptEditor
