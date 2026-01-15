import { Plus, Loader2 } from 'lucide-react'

/**
 * 블록 사이에 표시되는 새 블록 추가 버튼
 * @param {function} onAdd - 클릭 시 호출되는 콜백
 * @param {boolean} isLoading - 로딩 상태
 */
function AddBlockButton({ onAdd, isLoading = false }) {
  return (
    <button
      onClick={onAdd}
      disabled={isLoading}
      className="w-full py-2 flex items-center justify-center gap-1
                 text-gray-500 hover:text-primary
                 hover:bg-primary/10 rounded-lg transition-colors
                 disabled:opacity-50 disabled:cursor-not-allowed
                 touch-manipulation"
      title="Add new block"
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Plus className="w-4 h-4" />
      )}
    </button>
  )
}

export default AddBlockButton
