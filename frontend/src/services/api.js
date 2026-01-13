import axios from 'axios'
import logger from '../utils/logger'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:7100/api/v1',
  timeout: 300000, // LLM + Pexels 매칭 시간 고려 (5분)
})

// Trailing slash 제거 인터셉터
api.interceptors.request.use((config) => {
  if (config.url && config.url.endsWith('/')) {
    config.url = config.url.slice(0, -1)
  }
  logger.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data)
  return config
})

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    logger.debug(`API Response: ${response.status}`, response.data)
    return response
  },
  (error) => {
    const errorData = error.response?.data || { message: error.message }
    logger.error(`API Error: ${error.response?.status}`, errorData)
    return Promise.reject(error)
  }
)

/**
 * Project API
 */
export const projectApi = {
  /**
   * 프로젝트 생성
   * @param {Object} data - { script_raw, title? }
   */
  create: (data) => api.post('/projects', data),

  /**
   * 프로젝트 상세 조회
   * @param {string} id - 프로젝트 ID
   */
  get: (id) => api.get(`/projects/${id}`),

  /**
   * Generate 실행 (LLM 의미론적 분할 + 에셋 매칭)
   * @param {string} id - 프로젝트 ID
   * @param {Object} options - { max_candidates_per_block?, signal? }
   */
  generate: (id, options = {}) => {
    const { signal, ...generateOptions } = options
    return api.post(`/projects/${id}/generate`, generateOptions, { signal })
  },

  /**
   * 프로젝트의 블록 목록 조회
   * @param {string} id - 프로젝트 ID
   */
  getBlocks: (id) => api.get(`/projects/${id}/blocks`),
}

/**
 * Block API
 */
export const blockApi = {
  /**
   * 블록의 에셋 후보 목록 조회
   * @param {string} blockId - 블록 ID
   */
  getAssets: (blockId) => api.get(`/blocks/${blockId}/assets`),

  /**
   * 대표 에셋 선택
   * @param {string} blockId - 블록 ID
   * @param {string} assetId - 에셋 ID
   */
  setPrimary: (blockId, assetId) => api.post(`/blocks/${blockId}/primary`, { asset_id: assetId }),
}

export default api
