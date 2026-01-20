import { useState } from 'react'
import { AlertTriangle, CheckCircle, Copy, Loader2, FileText, ListChecks, FileCode, GitCompare } from 'lucide-react'
import toast from 'react-hot-toast'
import logger from '../../utils/logger'

/**
 * QA 결과 표시 컴포넌트
 * 4개 탭: 진단, 구조 점검, 보정 스크립트, 변경 로그
 */
function QAResultView({ qaResult }) {
  const [activeTab, setActiveTab] = useState('diagnosis')
  const [isCopyingCorrected, setIsCopyingCorrected] = useState(false)

  if (!qaResult) {
    return (
      <div className="text-gray-400 text-center py-12">
        QA 결과를 불러오는 중입니다...
      </div>
    )
  }

  const tabs = [
    { id: 'diagnosis', label: '진단', icon: AlertTriangle },
    { id: 'structure', label: '구조', icon: ListChecks },
    { id: 'corrected', label: '보정 스크립트', icon: FileCode },
    { id: 'changelog', label: '변경 로그', icon: GitCompare },
  ]

  // 보정 스크립트 복사
  const handleCopyCorrected = async () => {
    try {
      setIsCopyingCorrected(true)
      await navigator.clipboard.writeText(qaResult.corrected_script)
      toast.success('보정 스크립트가 클립보드에 복사되었습니다')
      logger.info('Corrected script copied to clipboard')
    } catch (err) {
      toast.error('복사 실패')
      logger.error('Failed to copy corrected script', { error: err.message })
    } finally {
      setIsCopyingCorrected(false)
    }
  }

  return (
    <div>
      {/* 탭 메뉴 */}
      <div className="flex border-b border-dark-border overflow-x-auto mb-6">
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="text-sm font-medium">{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* 탭 콘텐츠 */}
      <div>
        {activeTab === 'diagnosis' && <DiagnosisTab diagnosis={qaResult.diagnosis} />}
        {activeTab === 'structure' && <StructureTab structureCheck={qaResult.structure_check} />}
        {activeTab === 'corrected' && (
          <CorrectedScriptTab
            correctedScript={qaResult.corrected_script}
            isCopying={isCopyingCorrected}
            onCopy={handleCopyCorrected}
          />
        )}
        {activeTab === 'changelog' && <ChangeLogTab changeLogs={qaResult.change_logs} />}
      </div>

      {/* 푸터 (모델 정보) */}
      <div className="mt-6 pt-4 border-t border-dark-border text-xs text-gray-500">
        검증 모델: {qaResult.model} | 검증 시각: {new Date(qaResult.created_at).toLocaleString('ko-KR')}
      </div>
    </div>
  )
}

/**
 * 진단 탭
 */
function DiagnosisTab({ diagnosis }) {
  return (
    <div className="space-y-6">
      {/* 문제점 */}
      <div>
        <h3 className="text-base font-semibold text-red-400 mb-3 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          문제점
        </h3>
        <ul className="space-y-2">
          {diagnosis.problems.map((problem, index) => (
            <li key={index} className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
              <span className="text-red-400 font-bold mt-0.5">{index + 1}.</span>
              <span className="text-gray-200">{problem}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 장점 */}
      <div>
        <h3 className="text-base font-semibold text-green-400 mb-3 flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          장점
        </h3>
        <ul className="space-y-2">
          {diagnosis.strengths.map((strength, index) => (
            <li key={index} className="flex items-start gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <span className="text-green-400 font-bold mt-0.5">{index + 1}.</span>
              <span className="text-gray-200">{strength}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

/**
 * 구조 점검 탭
 */
function StructureTab({ structureCheck }) {
  const blocks = [
    { key: 'has_hook', label: 'Hook (시청자 관심 유도)' },
    { key: 'has_context', label: '맥락 (주제 배경 설명)' },
    { key: 'has_promise_outline', label: 'Promise + Outline (내용 예고)' },
    { key: 'has_body', label: 'Body (핵심 내용)' },
    { key: 'has_wrapup', label: 'Wrap-up (마무리)' },
  ]

  return (
    <div className="space-y-6">
      {/* 전체 통과 여부 */}
      <div className={`p-4 rounded-lg border ${
        structureCheck.overall_pass
          ? 'bg-green-500/10 border-green-500/30'
          : 'bg-red-500/10 border-red-500/30'
      }`}>
        <div className="flex items-center gap-2 mb-2">
          {structureCheck.overall_pass ? (
            <CheckCircle className="w-5 h-5 text-green-400" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-red-400" />
          )}
          <span className={`font-semibold ${
            structureCheck.overall_pass ? 'text-green-400' : 'text-red-400'
          }`}>
            {structureCheck.overall_pass ? '구조 검증 통과' : '구조 검증 실패'}
          </span>
        </div>
        {structureCheck.comments && (
          <p className="text-sm text-gray-300 mt-2">{structureCheck.comments}</p>
        )}
      </div>

      {/* 5블록 체크리스트 */}
      <div>
        <h3 className="text-base font-semibold text-gray-200 mb-3">5블록 구조 체크리스트</h3>
        <ul className="space-y-2">
          {blocks.map(block => {
            const isPassed = structureCheck[block.key]
            return (
              <li
                key={block.key}
                className={`flex items-center gap-3 p-3 rounded-lg border ${
                  isPassed
                    ? 'bg-green-500/5 border-green-500/20'
                    : 'bg-red-500/5 border-red-500/20'
                }`}
              >
                {isPassed ? (
                  <CheckCircle className="w-5 h-5 text-green-400" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                )}
                <span className="text-gray-200">{block.label}</span>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}

/**
 * 보정 스크립트 탭
 */
function CorrectedScriptTab({ correctedScript, isCopying, onCopy }) {
  return (
    <div className="space-y-4">
      {/* 복사 버튼 */}
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-gray-200">가이드라인에 맞게 보정된 최종 스크립트</h3>
        <button
          onClick={onCopy}
          disabled={isCopying}
          className="flex items-center gap-2 px-3 py-2 bg-dark-card border border-dark-border rounded-lg hover:bg-dark-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCopying ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Copy className="w-4 h-4" />
          )}
          <span className="text-sm">복사</span>
        </button>
      </div>

      {/* 보정 스크립트 텍스트 */}
      <div className="p-4 bg-dark-card border border-dark-border rounded-lg">
        <pre className="text-gray-200 whitespace-pre-wrap font-sans leading-relaxed">
          {correctedScript}
        </pre>
      </div>
    </div>
  )
}

/**
 * 변경 로그 탭
 */
function ChangeLogTab({ changeLogs }) {
  if (!changeLogs?.length) {
    return (
      <div className="text-gray-400 text-center py-12">
        변경 사항이 없습니다
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {changeLogs.map((log, index) => (
        <div
          key={index}
          className="flex items-start gap-3 p-3 bg-dark-card border border-dark-border rounded-lg"
        >
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-400">블록 {log.block_index + 1}</span>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
              log.change_type === '수정'
                ? 'bg-yellow-500/20 text-yellow-400'
                : log.change_type === '추가'
                ? 'bg-green-500/20 text-green-400'
                : 'bg-red-500/20 text-red-400'
            }`}>
              {log.change_type}
            </span>
          </div>
          <span className="text-gray-200 flex-1">{log.description}</span>
        </div>
      ))}
    </div>
  )
}

export default QAResultView
