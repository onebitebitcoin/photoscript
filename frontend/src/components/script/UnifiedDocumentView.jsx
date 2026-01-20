import { memo } from 'react'
import { renderTextWithLinks } from './EditableBlockCard'

/**
 * 통합 문서 보기 컴포넌트
 * 모든 블록을 하나의 문서로 합쳐서 표시 (읽기 전용)
 */
function UnifiedDocumentView({ blocks }) {
  if (!blocks?.length) {
    return (
      <div className="max-w-3xl mx-auto px-4 md:px-6 py-12 text-center">
        <p className="text-gray-400">표시할 블록이 없습니다</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-4 md:px-6 py-6">
      {blocks.map((block, index) => (
        <div key={block.id}>
          {/* 블록 번호 */}
          <div className="text-xs text-gray-500 mb-2">
            BLOCK {index + 1}
          </div>

          {/* 블록 텍스트 */}
          <div className="text-gray-200 whitespace-pre-wrap mb-6">
            {renderTextWithLinks(block.text)}
          </div>

          {/* 구분선 (마지막 블록 제외) */}
          {index < blocks.length - 1 && (
            <div className="border-b border-dark-border mb-6" />
          )}
        </div>
      ))}
    </div>
  )
}

export default memo(UnifiedDocumentView)
