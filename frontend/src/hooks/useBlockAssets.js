import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { blockApi } from '../services/api'
import logger from '../utils/logger'

/**
 * 블록의 에셋 데이터를 가져오는 훅
 * @param {string} blockId - 블록 ID
 */
export function useBlockAssets(blockId) {
  const [assets, setAssets] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchAssets = useCallback(async () => {
    if (!blockId) {
      setAssets([])
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const { data } = await blockApi.getAssets(blockId)
      setAssets(data)
      logger.info('Block assets loaded', { blockId, count: data.length })
    } catch (err) {
      logger.error('Failed to fetch block assets', { blockId, error: err })
      setError(err.response?.data?.detail?.message || err.message || 'Failed to load assets')
    } finally {
      setIsLoading(false)
    }
  }, [blockId])

  const setPrimary = useCallback(async (assetId) => {
    try {
      await blockApi.setPrimary(blockId, assetId)

      // 로컬 상태 업데이트
      setAssets(prev => prev.map(a => ({
        ...a,
        is_primary: a.asset_id === assetId
      })))

      toast.success('Primary asset updated')
      logger.info('Primary asset set', { blockId, assetId })

      return true
    } catch (err) {
      logger.error('Failed to set primary', { blockId, assetId, error: err })
      toast.error('Failed to set primary asset')
      return false
    }
  }, [blockId])

  useEffect(() => {
    fetchAssets()
  }, [fetchAssets])

  return {
    assets,
    isLoading,
    error,
    setPrimary,
    refetch: fetchAssets
  }
}

export default useBlockAssets
