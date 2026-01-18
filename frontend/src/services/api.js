import axios from 'axios'
import logger from '../utils/logger'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 300000, // LLM + Pexels 매칭 시간 고려 (5분)
})

// 토큰 저장/조회/삭제
const TOKEN_KEY = 'auth_token'

export const getStoredToken = () => localStorage.getItem(TOKEN_KEY)
export const setStoredToken = (token) => localStorage.setItem(TOKEN_KEY, token)
export const removeStoredToken = () => localStorage.removeItem(TOKEN_KEY)

// Trailing slash 제거 및 토큰 인터셉터
api.interceptors.request.use((config) => {
  // Trailing slash 제거
  if (config.url && config.url.endsWith('/')) {
    config.url = config.url.slice(0, -1)
  }

  // 토큰이 있으면 Authorization 헤더 추가
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
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

    // 401 에러 시 토큰 삭제
    if (error.response?.status === 401) {
      removeStoredToken()
    }

    return Promise.reject(error)
  }
)

/**
 * Auth API
 */
export const authApi = {
  /**
   * 회원가입
   * @param {Object} data - { nickname, password }
   */
  register: (data) => api.post('/auth/register', data),

  /**
   * 로그인
   * @param {Object} data - { nickname, password }
   */
  login: (data) => api.post('/auth/login', data),

  /**
   * 닉네임 중복체크
   * @param {string} nickname
   */
  checkNickname: (nickname) => api.post('/auth/check-nickname', { nickname }),

  /**
   * 현재 사용자 정보 조회
   */
  getMe: () => api.get('/auth/me'),
}

/**
 * Project API
 */
export const projectApi = {
  /**
   * 프로젝트 목록 조회 (최신순)
   */
  list: () => api.get('/projects'),

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
   * 프로젝트 삭제
   * @param {string} id - 프로젝트 ID
   */
  delete: (id) => api.delete(`/projects/${id}`),

  /**
   * Generate 실행 (LLM 의미론적 분할 + 에셋 매칭) - Quick Generate용
   * @param {string} id - 프로젝트 ID
   * @param {Object} options - { max_candidates_per_block?, signal? }
   */
  generate: (id, options = {}) => {
    const { signal, ...generateOptions } = options
    return api.post(`/projects/${id}/generate`, generateOptions, { signal })
  },

  /**
   * 스크립트 분할 (Step 1) - 에셋 매칭 없이 분할만
   * @param {string} id - 프로젝트 ID
   * @param {Object} options - { max_keywords?, signal? }
   */
  split: (id, options = {}) => {
    const { signal, ...splitOptions } = options
    return api.post(`/projects/${id}/split`, splitOptions, { signal })
  },

  /**
   * 에셋 매칭 실행 (Step 2) - 영상 우선 검색
   * @param {string} id - 프로젝트 ID
   * @param {Object} options - { max_candidates_per_block?, video_priority?, signal? }
   */
  match: (id, options = {}) => {
    const { signal, ...matchOptions } = options
    return api.post(`/projects/${id}/match`, matchOptions, { signal })
  },

  /**
   * 블록 합치기
   * @param {string} id - 프로젝트 ID
   * @param {string[]} blockIds - 합칠 블록 ID 목록
   */
  mergeBlocks: (id, blockIds) => api.post(`/projects/${id}/blocks/merge`, { block_ids: blockIds }),

  /**
   * 프로젝트의 블록 목록 조회
   * @param {string} id - 프로젝트 ID
   */
  getBlocks: (id) => api.get(`/projects/${id}/blocks`),

  /**
   * 새 블록 생성
   * @param {string} id - 프로젝트 ID
   * @param {Object} data - { text?, keywords?, insert_at }
   */
  createBlock: (id, data) => api.post(`/projects/${id}/blocks`, data),
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

  /**
   * 블록 수정
   * @param {string} blockId - 블록 ID
   * @param {Object} data - { text?, keywords? }
   */
  update: (blockId, data) => api.put(`/blocks/${blockId}`, data),

  /**
   * 블록 나누기
   * @param {string} blockId - 블록 ID
   * @param {number} splitPosition - 나눌 위치 (문자 인덱스)
   */
  split: (blockId, splitPosition) => api.post(`/blocks/${blockId}/split`, { split_position: splitPosition }),

  /**
   * 단일 블록 에셋 매칭
   * @param {string} blockId - 블록 ID
   * @param {Object} options - { video_priority?, max_candidates_per_block? }
   */
  match: (blockId, options = {}) => api.post(`/blocks/${blockId}/match`, options),

  /**
   * 키워드로 추가 에셋 검색
   * @param {string} blockId - 블록 ID
   * @param {string} keyword - 검색 키워드
   * @param {Object} options - { video_priority? }
   */
  search: (blockId, keyword, options = {}) => api.post(`/blocks/${blockId}/search`, { keyword, ...options }),

  /**
   * 블록 텍스트에서 키워드 자동 추출 (LLM)
   * @param {string} blockId - 블록 ID
   * @param {Object} options - { max_keywords? }
   */
  extractKeywords: (blockId, options = {}) => api.post(`/blocks/${blockId}/extract-keywords`, options),

  /**
   * 블록 삭제
   * @param {string} blockId - 블록 ID
   */
  delete: (blockId) => api.delete(`/blocks/${blockId}`),

  /**
   * AI로 블록 텍스트 자동 생성 (3가지 모드)
   * @param {string} blockId - 블록 ID
   * @param {Object} request - { mode: 'link'|'enhance'|'search', prompt: string, user_guide?: string }
   */
  generateText: (blockId, request) => api.post(`/blocks/${blockId}/generate-text`, request),
}

export default api
