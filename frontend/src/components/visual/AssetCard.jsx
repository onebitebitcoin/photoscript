import { Check, Image, Video, ExternalLink } from 'lucide-react'
import Button from '../common/Button'

/**
 * 에셋 카드 컴포넌트
 */
function AssetCard({ asset, isPrimary, onSelect, isSelecting }) {
  const { asset_type, thumbnail_url, source_url, title, provider } = asset.asset || asset

  return (
    <div className={`
      bg-dark-card border rounded-lg overflow-hidden group relative
      ${isPrimary ? 'border-primary' : 'border-dark-border hover:border-gray-600'}
    `}>
      {/* 이미지/비디오 썸네일 */}
      <div className="relative aspect-video bg-dark-bg">
        <img
          src={thumbnail_url}
          alt={title || 'Asset thumbnail'}
          className="w-full h-full object-cover"
        />

        {/* 대표 표시 */}
        {isPrimary && (
          <div className="absolute top-2 left-2 bg-primary text-white text-xs px-2 py-1 rounded flex items-center gap-1">
            <Check className="w-3 h-3" />
            Primary
          </div>
        )}

        {/* 타입 배지 */}
        <span className={`absolute top-2 right-2 text-xs px-1.5 py-0.5 rounded flex items-center gap-1 ${
          asset_type === 'VIDEO'
            ? 'bg-blue-500/80 text-white'
            : 'bg-green-500/80 text-white'
        }`}>
          {asset_type === 'VIDEO' ? <Video className="w-3 h-3" /> : <Image className="w-3 h-3" />}
        </span>

        {/* 호버 오버레이 */}
        {!isPrimary && (
          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <Button
              onClick={onSelect}
              loading={isSelecting}
              size="sm"
            >
              Use this
            </Button>
          </div>
        )}
      </div>

      {/* 정보 */}
      <div className="p-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400 capitalize">{provider}</span>
          <a
            href={source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-500 hover:text-white p-1"
            title="Open original"
          >
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        {title && (
          <p className="text-xs text-gray-300 truncate mt-1">{title}</p>
        )}
      </div>
    </div>
  )
}

export default AssetCard
