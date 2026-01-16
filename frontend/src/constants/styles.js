/**
 * 스타일 상수
 */
export const STYLES = {
  // 상태 배지 스타일
  STATUS_BADGE: {
    DRAFT: 'bg-yellow-500/20 text-yellow-400',
    MATCHED: 'bg-green-500/20 text-green-400',
    NO_RESULT: 'bg-red-500/20 text-red-400',
    PENDING: 'bg-blue-500/20 text-blue-400',
    CUSTOM: 'bg-purple-500/20 text-purple-400',
  },

  // 모드 배지 스타일
  MODE_BADGE: {
    link: 'bg-blue-500/20 text-blue-400',
    search: 'bg-purple-500/20 text-purple-400',
    enhance: 'bg-green-500/20 text-green-400',
  },

  // 에셋 타입 배지
  ASSET_TYPE_BADGE: {
    VIDEO: 'bg-blue-500',
    IMAGE: 'bg-green-500',
  },

  // 공통 버튼 스타일
  BUTTON: {
    ICON: 'p-1.5 hover:bg-dark-hover rounded transition-colors',
    ICON_DANGER: 'p-1.5 hover:bg-red-500/20 rounded transition-colors',
    PRIMARY: 'px-3 py-1.5 bg-primary hover:bg-primary-hover text-white rounded-md transition-colors',
    SECONDARY: 'px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors',
  },
}

/**
 * 상태에 따른 배지 클래스 반환
 * @param {string} status - 블록 상태
 * @returns {string} Tailwind CSS 클래스
 */
export function getStatusBadgeClass(status) {
  return STYLES.STATUS_BADGE[status] || STYLES.STATUS_BADGE.DRAFT
}

/**
 * 모드에 따른 배지 클래스 반환
 * @param {string} mode - 감지된 모드
 * @returns {string} Tailwind CSS 클래스
 */
export function getModeBadgeClass(mode) {
  return STYLES.MODE_BADGE[mode] || STYLES.MODE_BADGE.enhance
}

export default STYLES
