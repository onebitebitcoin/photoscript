import { useState, useEffect } from 'react'
import { Image, Video, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'

import AssetCard from './AssetCard'
import Loading from '../common/Loading'
import { blockApi } from '../../services/api'
import logger from '../../utils/logger'

/**
 * 비주얼 패널 컴포넌트
 */
function VisualPanel({ blockId, onAssetChange }) {
  const [assets, setAssets] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectingId, setSelectingId] = useState(null)

  // 블록 에셋 로드
  useEffect(() => {
    if (!blockId) {
      setAssets([])
      return
    }

    const fetchAssets = async () => {
      setIsLoading(true)
      try {
        const { data } = await blockApi.getAssets(blockId)
        setAssets(data)
        logger.info('Assets loaded', { blockId, count: data.length })
      } catch (err) {
        logger.error('Failed to load assets', err)
        toast.error('Failed to load assets')
      } finally {
        setIsLoading(false)
      }
    }

    fetchAssets()
  }, [blockId])

  // 대표 선택
  const handleSetPrimary = async (assetId) => {
    setSelectingId(assetId)
    try {
      await blockApi.setPrimary(blockId, assetId)

      // 로컬 상태 업데이트
      setAssets(prev => prev.map(a => ({
        ...a,
        is_primary: a.asset_id === assetId
      })))

      toast.success('Primary asset updated')
      logger.info('Primary asset set', { blockId, assetId })

      // 부모 컴포넌트에 변경 알림
      if (onAssetChange) onAssetChange()

    } catch (err) {
      logger.error('Failed to set primary', err)
      toast.error('Failed to set primary asset')
    } finally {
      setSelectingId(null)
    }
  }

  // 블록 미선택 상태
  if (!blockId) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <Image className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Select a segment to view visuals</p>
        </div>
      </div>
    )
  }

  // 로딩 중
  if (isLoading) {
    return <Loading message="Loading visuals..." />
  }

  // 에셋 없음
  if (assets.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <Image className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No visuals found for this segment</p>
          <p className="text-sm mt-1">Try refining the keywords</p>
        </div>
      </div>
    )
  }

  const primaryAsset = assets.find(a => a.is_primary)
  const candidates = assets.filter(a => !a.is_primary)

  return (
    <div className="p-4 space-y-6">
      {/* 대표 에셋 (크게 표시) */}
      {primaryAsset && (
        <div>
          <h3 className="text-xs font-medium text-gray-400 mb-2 uppercase">
            Primary Visual
          </h3>
          <div className="bg-dark-card border border-primary rounded-lg overflow-hidden">
            <div className="relative aspect-video bg-dark-bg">
              {primaryAsset.asset.asset_type === 'VIDEO' ? (
                <video
                  src={primaryAsset.asset.source_url}
                  poster={primaryAsset.asset.thumbnail_url}
                  controls
                  className="w-full h-full object-contain"
                />
              ) : (
                <img
                  src={primaryAsset.asset.source_url}
                  alt={primaryAsset.asset.title || 'Primary visual'}
                  className="w-full h-full object-contain"
                />
              )}

              {/* 타입 배지 */}
              <span className={`absolute top-2 right-2 text-xs px-2 py-1 rounded flex items-center gap-1 ${
                primaryAsset.asset.asset_type === 'VIDEO'
                  ? 'bg-blue-500 text-white'
                  : 'bg-green-500 text-white'
              }`}>
                {primaryAsset.asset.asset_type === 'VIDEO' ? (
                  <Video className="w-3 h-3" />
                ) : (
                  <Image className="w-3 h-3" />
                )}
                {primaryAsset.asset.asset_type}
              </span>
            </div>

            {/* 정보 */}
            <div className="p-3 flex items-center justify-between">
              <div>
                <span className="text-xs text-gray-400 capitalize">
                  {primaryAsset.asset.provider}
                </span>
                {primaryAsset.asset.title && (
                  <p className="text-sm text-white truncate">{primaryAsset.asset.title}</p>
                )}
              </div>
              <a
                href={primaryAsset.asset.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-white p-2"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      )}

      {/* 후보 갤러리 */}
      {candidates.length > 0 && (
        <div>
          <h3 className="text-xs font-medium text-gray-400 mb-2 uppercase">
            Candidates ({candidates.length})
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {candidates.map((asset) => (
              <AssetCard
                key={asset.id}
                asset={asset}
                isPrimary={false}
                onSelect={() => handleSetPrimary(asset.asset_id)}
                isSelecting={selectingId === asset.asset_id}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default VisualPanel
