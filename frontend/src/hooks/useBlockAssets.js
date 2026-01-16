import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { blockApi } from '../services/api'
import logger from '../utils/logger'
import { TOAST } from '../constants/messages'

/**
 * 블록의 에셋 데이터를 가져오는 훅
 * @param {string} blockId - 블록 ID
 * @param {string} blockStatus - 블록 상태 (MATCHED, CUSTOM 등)
 */
export function useBlockAssets(blockId, blockStatus) {
  const [assets, setAssets] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchAssets = useCallback(async () => {
    if (!blockId) {
      setAssets([])
      return
    }

    // 매칭된 상태에서만 에셋 로드
    if (blockStatus !== 'MATCHED' && blockStatus !== 'CUSTOM') {
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
      logger.error('Failed to fetch block assets', { blockId, error: err.message })
      setError(err.response?.data?.detail?.message || err.message || 'Failed to load assets')
    } finally {
      setIsLoading(false)
    }
  }, [blockId, blockStatus])

  const setPrimary = useCallback(async (assetId) => {
    try {
      await blockApi.setPrimary(blockId, assetId)

      // 로컬 상태 업데이트
      setAssets(prev => prev.map(a => ({
        ...a,
        is_primary: a.asset_id === assetId
      })))

      toast.success(TOAST.SUCCESS.ASSET_SELECTED)
      logger.info('Primary asset set', { blockId, assetId })

      return true
    } catch (err) {
      logger.error('Failed to set primary', { blockId, assetId, error: err.message })
      toast.error(TOAST.ERROR.SELECT_FAILED)
      return false
    }
  }, [blockId])

  /**
   * 키워드 매칭으로 에셋 검색
   * @param {Object} options - 옵션 (video_priority 등)
   */
  const matchAssets = useCallback(async (options = { video_priority: true }) => {
    try {
      await blockApi.match(blockId, options)
      const { data } = await blockApi.getAssets(blockId)
      setAssets(data)
      toast.success(TOAST.SUCCESS.ASSETS_FOUND(data.length))
      logger.info('Assets matched', { blockId, count: data.length })
      return data
    } catch (err) {
      logger.error('Failed to match assets', { blockId, error: err.message })
      toast.error(err.response?.data?.detail?.message || TOAST.ERROR.SEARCH_FAILED)
      throw err
    }
  }, [blockId])

  /**
   * 키워드로 에셋 검색
   * @param {string} keyword - 검색 키워드
   * @param {Object} options - 옵션
   */
  const searchByKeyword = useCallback(async (keyword, options = { video_priority: true }) => {
    if (!keyword.trim()) {
      toast.error(TOAST.ERROR.EMPTY_KEYWORD)
      return null
    }

    try {
      const { data: newAssets } = await blockApi.search(blockId, keyword.trim(), options)
      if (newAssets.length > 0) {
        setAssets(newAssets)
        toast.success(TOAST.SUCCESS.ASSETS_FOUND(newAssets.length))
        logger.info('Assets searched', { blockId, keyword, count: newAssets.length })
        return newAssets
      } else {
        toast.error(TOAST.ERROR.NO_SEARCH_RESULT)
        return []
      }
    } catch (err) {
      logger.error('Failed to search assets', { blockId, keyword, error: err.message })
      toast.error(err.response?.data?.detail?.message || TOAST.ERROR.KEYWORD_SEARCH_FAILED)
      throw err
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
    matchAssets,
    searchByKeyword,
    refetch: fetchAssets
  }
}

export default useBlockAssets
