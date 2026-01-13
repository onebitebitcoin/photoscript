import { useState, useEffect, useCallback } from 'react'
import { projectApi } from '../services/api'
import logger from '../utils/logger'

/**
 * 프로젝트 데이터를 가져오는 훅
 * @param {string} projectId - 프로젝트 ID
 */
export function useProject(projectId) {
  const [project, setProject] = useState(null)
  const [blocks, setBlocks] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchProject = useCallback(async () => {
    if (!projectId) {
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const { data } = await projectApi.get(projectId)
      setProject({
        id: data.id,
        title: data.title,
        script_raw: data.script_raw,
        created_at: data.created_at,
        updated_at: data.updated_at
      })
      setBlocks(data.blocks || [])
      logger.info('Project loaded', { projectId, blocksCount: data.blocks?.length })
    } catch (err) {
      logger.error('Failed to fetch project', { projectId, error: err })
      setError(err.response?.data?.detail?.message || err.message || 'Failed to load project')
    } finally {
      setIsLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchProject()
  }, [fetchProject])

  return {
    project,
    blocks,
    isLoading,
    error,
    refetch: fetchProject
  }
}

export default useProject
