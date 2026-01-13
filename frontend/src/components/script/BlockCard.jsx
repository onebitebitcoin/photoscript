import { Image, Video } from 'lucide-react'

const statusColors = {
  MATCHED: 'border-l-green-500',
  NO_RESULT: 'border-l-yellow-500',
  CUSTOM: 'border-l-blue-500',
  PENDING: 'border-l-gray-500',
}

const statusLabels = {
  MATCHED: 'Matched',
  NO_RESULT: 'No Result',
  CUSTOM: 'Custom',
  PENDING: 'Pending',
}

/**
 * 블록 카드 컴포넌트
 */
function BlockCard({ block, isSelected, onClick }) {
  const { index, text, keywords, status, primary_asset } = block

  return (
    <div
      onClick={onClick}
      className={`
        bg-dark-card rounded-lg p-3 cursor-pointer border-l-4
        ${statusColors[status] || statusColors.PENDING}
        ${isSelected ? 'ring-2 ring-primary' : 'hover:bg-dark-hover'}
        transition-all duration-200
      `}
    >
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-gray-400">
          SEGMENT {String(index + 1).padStart(2, '0')}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded ${
          status === 'MATCHED' ? 'bg-green-500/20 text-green-400' :
          status === 'CUSTOM' ? 'bg-blue-500/20 text-blue-400' :
          status === 'NO_RESULT' ? 'bg-yellow-500/20 text-yellow-400' :
          'bg-gray-500/20 text-gray-400'
        }`}>
          {statusLabels[status]}
        </span>
      </div>

      {/* 텍스트 */}
      <p className="text-sm text-white line-clamp-3 mb-2">
        {text}
      </p>

      {/* 키워드 */}
      {keywords && keywords.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {keywords.slice(0, 3).map((kw, i) => (
            <span
              key={i}
              className="text-xs bg-dark-bg px-2 py-0.5 rounded text-gray-400"
            >
              {kw}
            </span>
          ))}
          {keywords.length > 3 && (
            <span className="text-xs text-gray-500">+{keywords.length - 3}</span>
          )}
        </div>
      )}

      {/* 대표 에셋 썸네일 */}
      {primary_asset && (
        <div className="relative">
          <img
            src={primary_asset.thumbnail_url}
            alt=""
            className="w-full h-20 object-cover rounded"
          />
          <span className={`absolute bottom-1 right-1 text-xs px-1.5 py-0.5 rounded flex items-center gap-1 ${
            primary_asset.asset_type === 'VIDEO'
              ? 'bg-blue-500/80 text-white'
              : 'bg-green-500/80 text-white'
          }`}>
            {primary_asset.asset_type === 'VIDEO' ? (
              <Video className="w-3 h-3" />
            ) : (
              <Image className="w-3 h-3" />
            )}
            {primary_asset.asset_type}
          </span>
        </div>
      )}
    </div>
  )
}

export default BlockCard
