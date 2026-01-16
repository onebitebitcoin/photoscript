import { memo } from 'react'
import { Check, X } from 'lucide-react'

/**
 * 블록 텍스트 편집기
 * @param {string} text - 텍스트 내용
 * @param {function} onChange - 텍스트 변경 콜백
 * @param {function} onSave - 저장 콜백
 * @param {function} onCancel - 취소 콜백
 * @param {boolean} isSaving - 저장 중 여부
 */
function BlockTextEditor({ text, onChange, onSave, onCancel, isSaving }) {
  return (
    <>
      {/* 텍스트 영역 */}
      <textarea
        value={text}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-dark-bg border border-dark-border rounded-md p-2 text-sm text-white resize-none focus:outline-none focus:border-primary"
        rows={Math.min(20, Math.max(6, text.split('\n').length + 1))}
      />

      {/* 액션 버튼 */}
      <div className="flex justify-end gap-2 pt-2 border-t border-dark-border">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4 inline mr-1" />
          Cancel
        </button>
        <button
          onClick={onSave}
          disabled={isSaving}
          className="px-3 py-1.5 text-sm bg-primary hover:bg-primary-hover text-white rounded-md transition-colors disabled:opacity-50"
        >
          <Check className="w-4 h-4 inline mr-1" />
          {isSaving ? 'Saving...' : 'Save'}
        </button>
      </div>
    </>
  )
}

export default memo(BlockTextEditor)
