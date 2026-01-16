import { memo } from 'react'
import { X } from 'lucide-react'
import { STYLES } from '../../constants/styles'

/**
 * 에셋 미리보기 모달
 * @param {Object} asset - 에셋 데이터
 * @param {function} onClose - 닫기 콜백
 */
function AssetModal({ asset, onClose }) {
  if (!asset) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      onClick={onClose}
    >
      <div
        className="relative max-w-4xl max-h-[90vh] w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 닫기 버튼 */}
        <button
          onClick={onClose}
          className="absolute -top-10 right-0 p-2 text-white hover:text-gray-300 transition-colors"
        >
          <X className="w-6 h-6" />
        </button>

        {/* 미디어 콘텐츠 */}
        <div className="bg-dark-card rounded-lg overflow-hidden">
          {asset.asset_type === 'VIDEO' ? (
            <video
              src={asset.source_url}
              poster={asset.thumbnail_url}
              controls
              autoPlay
              className="w-full max-h-[70vh] object-contain"
            />
          ) : (
            <img
              src={asset.source_url}
              alt={asset.title || 'Image'}
              className="w-full max-h-[70vh] object-contain"
            />
          )}

          {/* 정보 */}
          <div className="p-3 border-t border-dark-border">
            <div className="flex items-center justify-between">
              <div>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  STYLES.ASSET_TYPE_BADGE[asset.asset_type] || STYLES.ASSET_TYPE_BADGE.IMAGE
                } text-white`}>
                  {asset.asset_type}
                </span>
                <span className="text-xs text-gray-400 ml-2 capitalize">
                  {asset.provider}
                </span>
              </div>
              <a
                href={asset.source_url}
                download
                className="text-xs text-primary hover:underline"
              >
                Download
              </a>
            </div>
            {asset.title && (
              <p className="text-sm text-white mt-2">{asset.title}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default memo(AssetModal)
