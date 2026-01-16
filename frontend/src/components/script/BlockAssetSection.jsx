import { memo, useState } from 'react'
import { Loader2, Check, Play, Eye, Video, Image, Search } from 'lucide-react'
import { STYLES } from '../../constants/styles'

/**
 * 개별 에셋 썸네일 카드
 */
function AssetThumbnail({ item, onSelect, onView, isSelecting }) {
  const asset = item.asset || item
  const hasPrimary = item._hasPrimary
  const isDimmed = hasPrimary && !item.is_primary

  return (
    <div
      className={`relative aspect-video bg-dark-bg rounded overflow-hidden group transition-all ${
        item.is_primary ? 'ring-2 ring-primary' : ''
      } ${isDimmed ? 'opacity-40 hover:opacity-100' : ''}`}
    >
      <img
        src={asset.thumbnail_url}
        alt={asset.title || 'Thumbnail'}
        className="w-full h-full object-cover"
      />
      {/* 호버 시 버튼 오버레이 */}
      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
        {/* 선택 버튼 */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onSelect(item.asset_id)
          }}
          disabled={isSelecting || item.is_primary}
          className={`p-1.5 rounded transition-colors ${
            item.is_primary
              ? 'bg-primary text-white'
              : 'bg-white/20 hover:bg-primary text-white'
          } disabled:opacity-50`}
          title={item.is_primary ? 'Selected' : 'Use this'}
        >
          {isSelecting ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Check className="w-3 h-3" />
          )}
        </button>
        {/* 보기 버튼 */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onView(asset)
          }}
          className="p-1.5 bg-white/20 hover:bg-white/40 rounded transition-colors text-white"
          title="View"
        >
          {asset.asset_type === 'VIDEO' ? (
            <Play className="w-3 h-3" />
          ) : (
            <Eye className="w-3 h-3" />
          )}
        </button>
      </div>
      {/* 타입 배지 */}
      <span className={`absolute top-0.5 right-0.5 p-0.5 rounded ${
        STYLES.ASSET_TYPE_BADGE[asset.asset_type] || STYLES.ASSET_TYPE_BADGE.IMAGE
      }`}>
        {asset.asset_type === 'VIDEO' ? (
          <Video className="w-2.5 h-2.5 text-white" />
        ) : (
          <Image className="w-2.5 h-2.5 text-white" />
        )}
      </span>
    </div>
  )
}

/**
 * 블록 에셋 섹션
 * @param {Array} assets - 에셋 목록
 * @param {boolean} isLoading - 로딩 중 여부
 * @param {function} onSelectAsset - 에셋 선택 콜백
 * @param {function} onKeywordSearch - 키워드 검색 콜백
 * @param {function} onViewAsset - 에셋 보기 콜백
 * @param {string|null} selectingAssetId - 선택 중인 에셋 ID
 */
function BlockAssetSection({
  assets,
  isLoading,
  onSelectAsset,
  onKeywordSearch,
  onViewAsset,
  selectingAssetId
}) {
  const [showCount, setShowCount] = useState(4)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [isSearching, setIsSearching] = useState(false)

  const handleSearch = async () => {
    if (!searchKeyword.trim()) return
    setIsSearching(true)
    try {
      await onKeywordSearch(searchKeyword.trim())
      setSearchKeyword('')
      setShowCount(4)
    } finally {
      setIsSearching(false)
    }
  }

  // primary 여부 미리 계산
  const hasPrimary = assets.some(a => a.is_primary)
  const enrichedAssets = assets.map(a => ({ ...a, _hasPrimary: hasPrimary }))

  return (
    <div>
      <p className="text-xs text-gray-500 mb-1.5">Visuals</p>

      {isLoading ? (
        <div className="flex items-center gap-2 text-gray-500 text-xs">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>Loading...</span>
        </div>
      ) : assets.length > 0 ? (
        <>
          <div className="grid grid-cols-4 gap-2">
            {enrichedAssets.slice(0, showCount).map((item) => (
              <AssetThumbnail
                key={item.id}
                item={item}
                onSelect={onSelectAsset}
                onView={onViewAsset}
                isSelecting={selectingAssetId === item.asset_id}
              />
            ))}
          </div>
          {/* 더보기 버튼 */}
          {assets.length > showCount && (
            <button
              onClick={() => setShowCount(prev => prev + 4)}
              className="w-full mt-2 py-1.5 text-xs text-gray-400 hover:text-white bg-dark-hover hover:bg-dark-border rounded transition-colors"
            >
              More ({assets.length - showCount} left)
            </button>
          )}
        </>
      ) : (
        <p className="text-xs text-gray-500">
          No visuals yet. Click search to find.
        </p>
      )}

      {/* 키워드 검색 */}
      <div className="flex gap-2 mt-2">
        <input
          type="text"
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search more..."
          className="flex-1 bg-dark-bg border border-dark-border rounded px-2 py-1 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-primary"
        />
        <button
          onClick={handleSearch}
          disabled={isSearching}
          className="px-2 py-1 bg-dark-hover hover:bg-primary/20 rounded text-xs text-gray-400 hover:text-white transition-colors disabled:opacity-50"
        >
          {isSearching ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Search className="w-3 h-3" />
          )}
        </button>
      </div>
    </div>
  )
}

export default memo(BlockAssetSection)
