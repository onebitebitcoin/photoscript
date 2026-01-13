import BlockCard from './BlockCard'
import Loading from '../common/Loading'

/**
 * 블록 리스트 컴포넌트
 */
function BlockList({ blocks, selectedId, onSelect, isLoading }) {
  if (isLoading) {
    return <Loading message="Loading blocks..." />
  }

  if (!blocks || blocks.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No blocks found
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {blocks.map((block) => (
        <BlockCard
          key={block.id}
          block={block}
          isSelected={selectedId === block.id}
          onClick={() => onSelect(block.id)}
        />
      ))}
    </div>
  )
}

export default BlockList
