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
        <div key={block.id} className={index < blocks.length - 1 ? 'mb-8' : ''}>
          <div className="text-gray-200 whitespace-pre-wrap">
            {renderTextWithLinks(block.text)}
          </div>
        </div>
      ))}
    </div>
  )
}

export default memo(UnifiedDocumentView)
