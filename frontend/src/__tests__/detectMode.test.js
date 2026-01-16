/**
 * detectMode 유틸리티 함수 테스트
 *
 * 테스트 대상:
 * - detectMode(): 프롬프트 자동 모드 판단
 * - parseTextWithUrls(): 텍스트에서 URL 분리
 */

import { describe, it, expect } from 'vitest'
import { detectMode, parseTextWithUrls } from '../utils/detectMode'

describe('detectMode', () => {
  describe('LINK 모드 감지', () => {
    it('URL만 있을 때 LINK 모드', () => {
      const result = detectMode('https://example.com/article')

      expect(result.mode).toBe('link')
      expect(result.label).toBe('링크')
    })

    it('URL + 가이드 텍스트가 있을 때 LINK 모드', () => {
      const result = detectMode('https://example.com 이 내용 참고해서 작성해줘')

      expect(result.mode).toBe('link')
    })

    it('가이드가 URL 앞에 있을 때도 LINK 모드', () => {
      const result = detectMode('이 링크 참고해서 https://example.com/page 작성해줘')

      expect(result.mode).toBe('link')
    })

    it('HTTP URL도 LINK 모드', () => {
      const result = detectMode('http://example.com')

      expect(result.mode).toBe('link')
    })
  })

  describe('SEARCH 모드 감지', () => {
    it('검색해서 키워드로 SEARCH 모드', () => {
      const result = detectMode('AI 트렌드 검색해서 작성해줘')

      expect(result.mode).toBe('search')
      expect(result.label).toBe('검색')
    })

    it('찾아서 키워드로 SEARCH 모드', () => {
      const result = detectMode('최신 뉴스 찾아서 요약해줘')

      expect(result.mode).toBe('search')
    })

    it('알아봐서 키워드로 SEARCH 모드', () => {
      const result = detectMode('파이썬 버전 알아봐서 알려줘')

      expect(result.mode).toBe('search')
    })

    it('검색해줘 키워드로 SEARCH 모드', () => {
      const result = detectMode('React 최신 버전 검색해줘')

      expect(result.mode).toBe('search')
    })

    it('찾아줘 키워드로 SEARCH 모드', () => {
      const result = detectMode('날씨 정보 찾아줘')

      expect(result.mode).toBe('search')
    })

    it('알아봐줘 키워드로 SEARCH 모드', () => {
      const result = detectMode('주가 정보 알아봐줘')

      expect(result.mode).toBe('search')
    })
  })

  describe('ENHANCE 모드 감지', () => {
    it('일반 텍스트는 ENHANCE 모드', () => {
      const result = detectMode('위 내용을 더 자세히 설명해줘')

      expect(result.mode).toBe('enhance')
      expect(result.label).toBe('보완')
    })

    it('확장 요청도 ENHANCE 모드', () => {
      const result = detectMode('이 부분을 5문장으로 늘려줘')

      expect(result.mode).toBe('enhance')
    })

    it('빈 입력은 ENHANCE 모드', () => {
      const result = detectMode('')

      expect(result.mode).toBe('enhance')
    })

    it('공백만 있는 입력은 ENHANCE 모드', () => {
      const result = detectMode('   ')

      expect(result.mode).toBe('enhance')
    })

    it('null 입력은 ENHANCE 모드', () => {
      const result = detectMode(null)

      expect(result.mode).toBe('enhance')
    })

    it('undefined 입력은 ENHANCE 모드', () => {
      const result = detectMode(undefined)

      expect(result.mode).toBe('enhance')
    })
  })

  describe('우선순위 테스트', () => {
    it('URL이 있으면 검색 키워드가 있어도 LINK 모드', () => {
      const result = detectMode('https://example.com 검색해서 비교해줘')

      // URL이 있으므로 LINK 모드가 우선
      expect(result.mode).toBe('link')
    })
  })

  describe('공백 처리', () => {
    it('앞뒤 공백 제거 후 판단', () => {
      const result = detectMode('   간단한 텍스트   ')

      expect(result.mode).toBe('enhance')
    })
  })
})

describe('parseTextWithUrls', () => {
  it('URL 없는 텍스트', () => {
    const result = parseTextWithUrls('일반 텍스트입니다.')

    expect(result).toHaveLength(1)
    expect(result[0]).toEqual({ type: 'text', content: '일반 텍스트입니다.' })
  })

  it('URL만 있는 텍스트', () => {
    const result = parseTextWithUrls('https://example.com')

    expect(result).toHaveLength(1)
    expect(result[0]).toEqual({ type: 'url', content: 'https://example.com' })
  })

  it('텍스트 + URL 혼합', () => {
    const result = parseTextWithUrls('내용입니다. 출처: https://example.com 여기까지')

    expect(result).toHaveLength(3)
    expect(result[0].type).toBe('text')
    expect(result[1].type).toBe('url')
    expect(result[1].content).toBe('https://example.com')
    expect(result[2].type).toBe('text')
  })

  it('여러 URL이 있는 텍스트', () => {
    const result = parseTextWithUrls('링크1: https://a.com 링크2: https://b.com')

    const urls = result.filter(r => r.type === 'url')
    expect(urls).toHaveLength(2)
  })

  it('빈 텍스트', () => {
    const result = parseTextWithUrls('')

    expect(result).toHaveLength(0)
  })

  it('null 텍스트', () => {
    const result = parseTextWithUrls(null)

    expect(result).toHaveLength(0)
  })
})
