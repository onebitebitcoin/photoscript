/**
 * 토스트 메시지 상수
 */
export const TOAST = {
  SUCCESS: {
    BLOCK_UPDATED: '블록이 수정되었습니다',
    ASSET_SELECTED: 'Selected',
    TEXT_GENERATED: '텍스트가 생성되었습니다',
    ASSETS_FOUND: (count) => `${count}개 에셋 찾음`,
  },
  ERROR: {
    NO_KEYWORD: '키워드가 없습니다. 먼저 키워드를 추가해주세요.',
    SEARCH_FAILED: '에셋 검색에 실패했습니다',
    SELECT_FAILED: 'Failed to select',
    NO_SEARCH_RESULT: '검색 결과가 없습니다',
    KEYWORD_SEARCH_FAILED: '검색에 실패했습니다',
    EMPTY_KEYWORD: '키워드를 입력해주세요',
    EMPTY_PROMPT: '프롬프트를 입력해주세요',
    TEXT_GENERATION_FAILED: '텍스트 생성에 실패했습니다',
  }
}

export default TOAST
