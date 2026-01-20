import { useState, useEffect } from 'react'
import { Save, RotateCcw, Eye } from 'lucide-react'
import toast from 'react-hot-toast'
import { userApi } from '../services/api'
import logger from '../utils/logger'

function SettingsPage() {
  const [customGuideline, setCustomGuideline] = useState('')
  const [originalGuideline, setOriginalGuideline] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [showDefaultPreview, setShowDefaultPreview] = useState(false)

  // 기본 가이드라인 (하드코딩)
  const DEFAULT_GUIDELINE = `## 유튜브 스크립트 작성 가이드라인

### 권장 규칙
1. **입니다/합니다체 권장**: 문장 종결 시 "~입니다", "~합니다"체 사용 권장
2. **지시어 최소화**: "이것", "그것", "자 이제", "여러분" 등 지시어 사용 최소화
3. **AI 진행 멘트 최소화**: "다음으로 넘어가서", "이제 설명하겠습니다" 등 최소화
4. **다음 영상 예고 제한**: "다음 영상에서는..." 등 예고성 멘트 제한
5. **자연스러운 리듬**: 문장이 너무 끊기지 않고 자연스럽게 흐르도록

### 5블록 구조 (권장)
1. **Hook**: 시청자 관심 유도 (1~2문장)
2. **맥락**: 주제 배경 설명 (2~3문장)
3. **Promise + Outline**: 영상에서 다룰 내용 예고 (2~3문장)
4. **Body**: 핵심 내용 전달 (메인 콘텐츠)
5. **Wrap-up**: 마무리 및 요약 (1~2문장)

### 보정 원칙
- **원본 내용과 길이 완전 유지**: 절대로 내용을 줄이거나 요약하지 말 것
- **형식만 수정**: 문체, 지시어 제거 등 형식과 표현만 수정
- **정보 보존**: 원본의 모든 정보, 예시, 설명을 그대로 유지

### 진단 기준
- 문제점 3개: 가이드라인 개선 사항
- 장점 2개: 잘 작성된 부분`

  // 설정 불러오기
  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      setIsLoading(true)
      const { data } = await userApi.getSettings()
      const guideline = data.qa_custom_guideline || ''
      setCustomGuideline(guideline)
      setOriginalGuideline(guideline)
      logger.info('Settings loaded', { hasCustom: !!guideline })
    } catch (err) {
      toast.error('설정 불러오기 실패')
      logger.error('Failed to load settings', { error: err.message })
    } finally {
      setIsLoading(false)
    }
  }

  // 저장
  const handleSave = async () => {
    try {
      setIsSaving(true)
      await userApi.updateSettings({
        qa_custom_guideline: customGuideline || null
      })
      setOriginalGuideline(customGuideline)
      toast.success('설정이 저장되었습니다')
      logger.info('Settings saved', { length: customGuideline.length })
    } catch (err) {
      toast.error('설정 저장 실패')
      logger.error('Failed to save settings', { error: err.message })
    } finally {
      setIsSaving(false)
    }
  }

  // 초기화
  const handleReset = async () => {
    if (!confirm('설정을 초기화하시겠습니까? 기본 가이드라인이 적용됩니다.')) return

    try {
      setIsSaving(true)
      await userApi.resetSettings()
      setCustomGuideline('')
      setOriginalGuideline('')
      toast.success('설정이 초기화되었습니다')
      logger.info('Settings reset')
    } catch (err) {
      toast.error('초기화 실패')
      logger.error('Failed to reset settings', { error: err.message })
    } finally {
      setIsSaving(false)
    }
  }

  const hasChanges = customGuideline !== originalGuideline
  const isUsingDefault = !customGuideline

  return (
    <div className="min-h-screen bg-dark-bg p-4 md:p-6 overflow-x-hidden">
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-100 mb-2">설정</h1>
          <p className="text-gray-400 text-sm">
            QA 검증에 사용되는 가이드라인을 커스터마이징할 수 있습니다
          </p>
        </div>

        {/* QA 가이드라인 섹션 */}
        <div className="bg-dark-card border border-dark-border rounded-lg p-4 sm:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-100">
                QA 가이드라인
              </h2>
              <p className="text-sm text-gray-400 mt-1">
                {isUsingDefault ? '기본 가이드라인 사용 중' : '커스텀 가이드라인 사용 중'}
              </p>
            </div>

            <button
              onClick={() => setShowDefaultPreview(!showDefaultPreview)}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-dark-hover border border-dark-border rounded-lg hover:bg-dark-card transition-colors whitespace-nowrap self-start sm:self-auto"
            >
              <Eye className="w-4 h-4" />
              <span>기본 가이드라인 {showDefaultPreview ? '숨기기' : '보기'}</span>
            </button>
          </div>

          {/* 기본 가이드라인 프리뷰 */}
          {showDefaultPreview && (
            <div className="mb-4 p-4 bg-dark-bg border border-dark-border rounded-lg">
              <p className="text-xs text-gray-500 mb-2">기본 가이드라인 (읽기 전용)</p>
              <pre className="text-sm text-gray-300 whitespace-pre-wrap">
                {DEFAULT_GUIDELINE}
              </pre>
            </div>
          )}

          {/* 커스텀 가이드라인 편집기 */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-300">
              커스텀 가이드라인
            </label>
            <textarea
              value={customGuideline}
              onChange={(e) => setCustomGuideline(e.target.value)}
              placeholder="커스텀 가이드라인을 입력하세요. 비워두면 기본 가이드라인이 사용됩니다."
              rows={15}
              maxLength={10000}
              disabled={isLoading}
              className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y disabled:opacity-50"
            />

            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>
                {hasChanges && <span className="text-yellow-500">• 저장되지 않은 변경사항</span>}
              </span>
              <span>{customGuideline.length} / 10,000</span>
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="flex items-center gap-2 sm:gap-3 mt-6 flex-wrap">
            <button
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              <Save className="w-4 h-4" />
              <span className="text-sm sm:text-base">{isSaving ? '저장 중...' : '저장'}</span>
            </button>

            <button
              onClick={handleReset}
              disabled={isUsingDefault || isSaving}
              className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-dark-hover border border-dark-border text-gray-300 rounded-lg hover:bg-dark-card transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              <RotateCcw className="w-4 h-4" />
              <span className="text-sm sm:text-base">초기화</span>
            </button>
          </div>
        </div>

        {/* 안내 메시지 */}
        <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <p className="text-sm text-blue-400">
            팁: 커스텀 가이드라인은 모든 프로젝트의 QA 검증에 적용됩니다.
            프로젝트마다 다른 스타일이 필요한 경우 추가 프롬프트 기능을 활용하세요.
          </p>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
