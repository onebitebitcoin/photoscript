/**
 * 프롬프트에서 모드를 자동 감지
 * @param {string} prompt - 사용자 입력
 * @returns {{ mode: 'link' | 'search' | 'enhance', label: string, description: string }}
 */
export function detectMode(prompt) {
  const trimmed = (prompt || '').trim()

  // 빈 입력
  if (!trimmed) {
    return { mode: 'enhance', label: '보완', description: '컨텍스트 기반 생성' }
  }

  // 1. URL 패턴 확인
  if (/https?:\/\/[^\s]+/.test(trimmed)) {
    return { mode: 'link', label: '링크', description: 'URL 콘텐츠 참고' }
  }

  // 2. 검색 키워드 확인
  const searchKeywords = ['검색해서', '찾아서', '검색해줘', '찾아줘', '알아봐서', '알아봐줘']
  for (const kw of searchKeywords) {
    if (trimmed.includes(kw)) {
      return { mode: 'search', label: '검색', description: '웹 검색 후 생성' }
    }
  }

  // 3. 그 외: 보완 모드
  return { mode: 'enhance', label: '보완', description: '컨텍스트 기반 생성' }
}

/**
 * 텍스트에서 URL을 감지하여 분리
 * @param {string} text - 원본 텍스트
 * @returns {{ type: 'text' | 'url', content: string }[]}
 */
export function parseTextWithUrls(text) {
  if (!text) return []

  const urlPattern = /(https?:\/\/[^\s]+)/g
  const parts = text.split(urlPattern)

  return parts
    .filter(part => part) // 빈 문자열 제거
    .map(part => ({
      type: /^https?:\/\//.test(part) ? 'url' : 'text',
      content: part
    }))
}

export default detectMode
