import { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle, Copy, Loader2, FileText, ListChecks, FileCode, GitCompare, History, Edit2, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import logger from '../../utils/logger'
import { projectApi } from '../../services/api'

/**
 * QA 결과 표시 컴포넌트
 * 5개 탭: 진단, 구조 점검, 보정 스크립트, 변경 로그, 버전 목록
 */
function QAResultView({ qaResult, projectId }) {
  const [activeTab, setActiveTab] = useState('diagnosis')
  const [isCopyingCorrected, setIsCopyingCorrected] = useState(false)
  const [versions, setVersions] = useState([])
  const [isLoadingVersions, setIsLoadingVersions] = useState(false)

  if (!qaResult) {
    return (
      <div className="text-gray-400 text-center py-12">
        QA 결과를 불러오는 중입니다...
      </div>
    )
  }

  // 버전 목록 불러오기
  const loadVersions = async () => {
    if (!projectId) return
    try {
      setIsLoadingVersions(true)
      const { data } = await projectApi.getQAVersions(projectId)
      setVersions(data)
      logger.info('QA versions loaded', { count: data.length })
    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      toast.error(`버전 목록 불러오기 실패: ${message}`)
      logger.error('Failed to load QA versions', { error: message })
    } finally {
      setIsLoadingVersions(false)
    }
  }

  // 버전 탭 활성화 시 버전 목록 로드
  useEffect(() => {
    if (activeTab === 'versions') {
      loadVersions()
    }
  }, [activeTab])

  const tabs = [
    { id: 'diagnosis', label: '진단', icon: AlertTriangle },
    { id: 'structure', label: '구조', icon: ListChecks },
    { id: 'corrected', label: '보정 스크립트', icon: FileCode },
    { id: 'changelog', label: '변경 로그', icon: GitCompare },
    { id: 'versions', label: '버전 목록', icon: History },
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
        {activeTab === 'versions' && (
          <VersionsTab
            projectId={projectId}
            versions={versions}
            isLoading={isLoadingVersions}
            onRefresh={loadVersions}
          />
        )}
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

/**
 * 버전 목록 탭
 */
function VersionsTab({ projectId, versions, isLoading, onRefresh }) {
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState({ version_name: '', memo: '' })
  const [selectedVersion, setSelectedVersion] = useState(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)

  // 버전 상세 보기
  const handleView = async (versionId) => {
    try {
      setIsLoadingDetail(true)
      const { data } = await projectApi.getQAVersion(projectId, versionId)
      setSelectedVersion(data)
      logger.info('QA version detail loaded', { versionId })
    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      toast.error(`버전 상세 불러오기 실패: ${message}`)
      logger.error('Failed to load QA version detail', { error: message })
    } finally {
      setIsLoadingDetail(false)
    }
  }

  // 편집 모드 활성화
  const handleEdit = (version) => {
    setEditingId(version.id)
    setEditForm({
      version_name: version.version_name || '',
      memo: version.memo || ''
    })
  }

  // 편집 취소
  const handleCancel = () => {
    setEditingId(null)
    setEditForm({ version_name: '', memo: '' })
  }

  // 편집 저장
  const handleSave = async (versionId) => {
    try {
      await projectApi.updateQAVersion(projectId, versionId, editForm)
      toast.success('버전 정보가 수정되었습니다')
      setEditingId(null)
      onRefresh()
      logger.info('QA version updated', { versionId })
    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      toast.error(`버전 수정 실패: ${message}`)
      logger.error('Failed to update QA version', { error: message })
    }
  }

  // 버전 삭제
  const handleDelete = async (versionId) => {
    if (!confirm('이 버전을 삭제하시겠습니까?')) return

    try {
      await projectApi.deleteQAVersion(projectId, versionId)
      toast.success('버전이 삭제되었습니다')
      if (selectedVersion?.id === versionId) {
        setSelectedVersion(null)
      }
      onRefresh()
      logger.info('QA version deleted', { versionId })
    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      toast.error(`버전 삭제 실패: ${message}`)
      logger.error('Failed to delete QA version', { error: message })
    }
  }

  // 스크립트 복사
  const handleCopyScript = async (script) => {
    try {
      await navigator.clipboard.writeText(script)
      toast.success('스크립트가 클립보드에 복사되었습니다')
      logger.info('Version script copied to clipboard')
    } catch (err) {
      toast.error('복사 실패')
      logger.error('Failed to copy version script', { error: err.message })
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    )
  }

  if (!versions?.length) {
    return (
      <div className="text-gray-400 text-center py-12">
        저장된 버전이 없습니다
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 버전 목록 */}
      {versions.map((version, index) => (
        <div
          key={version.id}
          className="p-4 bg-dark-card border border-dark-border rounded-lg"
        >
          {editingId === version.id ? (
            // 편집 모드
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">버전 이름</label>
                <input
                  type="text"
                  value={editForm.version_name}
                  onChange={(e) => setEditForm({ ...editForm, version_name: e.target.value })}
                  placeholder="버전 이름 (선택사항)"
                  maxLength={255}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">메모</label>
                <textarea
                  value={editForm.memo}
                  onChange={(e) => setEditForm({ ...editForm, memo: e.target.value })}
                  placeholder="메모 (선택사항)"
                  rows={3}
                  maxLength={5000}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleSave(version.id)}
                  className="px-3 py-1.5 bg-primary/10 border border-primary/30 text-primary rounded hover:bg-primary/20 transition-colors text-sm"
                >
                  저장
                </button>
                <button
                  onClick={handleCancel}
                  className="px-3 py-1.5 bg-dark-hover border border-dark-border text-gray-400 rounded hover:bg-dark-card transition-colors text-sm"
                >
                  취소
                </button>
              </div>
            </div>
          ) : (
            // 보기 모드
            <div>
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-gray-200">
                      v{version.version_number}
                    </span>
                    {version.version_name && (
                      <span className="text-sm text-gray-300">
                        {version.version_name}
                      </span>
                    )}
                    {index === 0 && (
                      <span className="px-2 py-0.5 bg-primary/20 text-primary text-xs rounded">
                        최신
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(version.created_at).toLocaleString('ko-KR')} | {version.model}
                  </div>
                  {version.memo && (
                    <div className="mt-2 text-sm text-gray-400">
                      {version.memo}
                    </div>
                  )}
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleView(version.id)}
                    className="p-1.5 text-gray-400 hover:text-gray-200 transition-colors"
                    title="상세 보기"
                  >
                    <FileText className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleEdit(version)}
                    className="p-1.5 text-gray-400 hover:text-gray-200 transition-colors"
                    title="편집"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(version.id)}
                    className="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
                    title="삭제"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}

      {/* 선택된 버전 상세 보기 */}
      {selectedVersion && (
        <div className="mt-6 pt-6 border-t border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-gray-200">
              v{selectedVersion.version_number} 스크립트
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => handleCopyScript(selectedVersion.corrected_script)}
                className="flex items-center gap-1 px-3 py-1.5 bg-dark-card border border-dark-border rounded hover:bg-dark-hover transition-colors text-sm"
              >
                <Copy className="w-3 h-3" />
                <span>복사</span>
              </button>
              <button
                onClick={() => setSelectedVersion(null)}
                className="px-3 py-1.5 bg-dark-card border border-dark-border rounded hover:bg-dark-hover transition-colors text-sm"
              >
                닫기
              </button>
            </div>
          </div>
          <pre className="bg-dark-bg p-4 rounded-lg border border-dark-border overflow-x-auto text-sm text-gray-200 whitespace-pre-wrap">
            {selectedVersion.corrected_script}
          </pre>
        </div>
      )}
    </div>
  )
}

export default QAResultView
