import { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle, Copy, Loader2, FileText, ListChecks, FileCode, GitCompare, History, Edit2, Trash2, FilePlus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import ReactDiffViewer from 'react-diff-viewer-continued'
import toast from 'react-hot-toast'
import logger from '../../utils/logger'
import { projectApi } from '../../services/api'

/**
 * QA 결과 표시 컴포넌트
 * 5개 탭: 진단, 구조 점검, 보정 스크립트, 변경 로그, 버전 목록
 */
function QAResultView({ qaResult, projectId, originalTitle, initialTab = 'diagnosis' }) {
  const [activeTab, setActiveTab] = useState(initialTab)
  const [isCopyingCorrected, setIsCopyingCorrected] = useState(false)
  const [versions, setVersions] = useState([])
  const [isLoadingVersions, setIsLoadingVersions] = useState(false)

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
          // qaResult가 없으면 versions 탭만 활성화
          const isDisabled = !qaResult && tab.id !== 'versions'
          return (
            <button
              key={tab.id}
              onClick={() => !isDisabled && setActiveTab(tab.id)}
              disabled={isDisabled}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : isDisabled
                  ? 'border-transparent text-gray-600 cursor-not-allowed'
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
        {activeTab === 'diagnosis' && qaResult && <DiagnosisTab diagnosis={qaResult.diagnosis} />}
        {activeTab === 'structure' && qaResult && <StructureTab structureCheck={qaResult.structure_check} />}
        {activeTab === 'corrected' && qaResult && (
          <CorrectedScriptTab
            correctedScript={qaResult.corrected_script}
            isCopying={isCopyingCorrected}
            onCopy={handleCopyCorrected}
          />
        )}
        {activeTab === 'changelog' && qaResult && <ChangeLogTab changeLogs={qaResult.change_logs} />}
        {activeTab === 'versions' && (
          <VersionsTab
            projectId={projectId}
            versions={versions}
            isLoading={isLoadingVersions}
            onRefresh={loadVersions}
          />
        )}
      </div>

      {/* 푸터 (모델 정보) - qaResult가 있을 때만 표시 */}
      {qaResult && (
        <div className="mt-6 pt-4 border-t border-dark-border text-xs text-gray-500 space-y-1">
          <div>검증 모델: {qaResult.model} | 검증 시각: {new Date(qaResult.created_at).toLocaleString('ko-KR')}</div>
          {(qaResult.input_tokens || qaResult.output_tokens) && (
            <div>
              입력 토큰: {qaResult.input_tokens?.toLocaleString() || 'N/A'} |
              출력 토큰: {qaResult.output_tokens?.toLocaleString() || 'N/A'}
            </div>
          )}
        </div>
      )}
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
      {/* 헤더 및 버튼 */}
      <div className="flex items-center justify-between gap-2 flex-wrap mb-4">
        <h3 className="text-sm sm:text-base font-semibold text-gray-200">
          가이드라인에 맞게 보정된 최종 스크립트
        </h3>

        {/* 복사 버튼 */}
        <button
          onClick={onCopy}
          disabled={isCopying}
          className="flex items-center gap-1.5 px-3 py-2 bg-dark-card border border-dark-border rounded-lg hover:bg-dark-hover transition-colors disabled:opacity-50 text-sm"
        >
          {isCopying ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Copy className="w-4 h-4" />
          )}
          <span>복사</span>
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
  const navigate = useNavigate()
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState({ version_name: '', memo: '' })
  const [selectedVersion, setSelectedVersion] = useState(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)

  // 원본 프로젝트 정보
  const [originalScript, setOriginalScript] = useState(null)
  const [isLoadingProject, setIsLoadingProject] = useState(false)

  // 새 프로젝트 생성 관련
  const [isCreatingProject, setIsCreatingProject] = useState(false)

  // Diff 비교 관련 상태
  const [comparisonMode, setComparisonMode] = useState(false)
  const [selectedVersions, setSelectedVersions] = useState([]) // 최대 2개 ('v0' 또는 versionId)
  const [diffData, setDiffData] = useState(null) // { old, new }
  const [isLoadingDiff, setIsLoadingDiff] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // 원본 프로젝트 정보 불러오기
  const loadOriginalScript = async () => {
    if (!projectId || originalScript) return
    try {
      setIsLoadingProject(true)
      const { data } = await projectApi.get(projectId)
      setOriginalScript(data.script_raw)
      logger.info('Original script loaded for comparison')
    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      toast.error(`원본 스크립트 불러오기 실패: ${message}`)
      logger.error('Failed to load original script', { error: message })
    } finally {
      setIsLoadingProject(false)
    }
  }

  // 비교 모드 활성화 시 원본 스크립트 로드
  useEffect(() => {
    if (comparisonMode) {
      loadOriginalScript()
    }
  }, [comparisonMode])

  // 모바일 감지
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

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

  // 버전 스크립트로 새 프로젝트 생성
  const handleCreateProjectFromVersion = async (version) => {
    try {
      setIsCreatingProject(true)

      // 1. 새 프로젝트 생성
      const newTitle = version.version_name
        ? `${version.version_name} (v${version.version_number})`
        : `QA v${version.version_number} - ${new Date().toLocaleDateString('ko-KR')}`

      toast.loading('새 프로젝트 생성 중...', { id: 'create-version-project' })

      const { data: newProject } = await projectApi.create({
        script_raw: version.corrected_script,
        title: newTitle
      })

      logger.info('New project created from version', {
        projectId: newProject.id,
        versionId: version.id
      })

      // 2. 블록 자동 분할
      toast.loading('스크립트 분석 중...', { id: 'create-version-project' })
      await projectApi.split(newProject.id)

      logger.info('Version project split completed', {
        projectId: newProject.id
      })

      // 3. 성공 메시지
      toast.success('새 프로젝트가 생성되었습니다!', {
        id: 'create-version-project'
      })

      // 4. 편집 페이지로 이동
      navigate(`/project/${newProject.id}/edit`)

    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      toast.error(`프로젝트 생성 실패: ${message}`, {
        id: 'create-version-project'
      })
      logger.error('Failed to create project from version', {
        error: message,
        versionId: version.id
      })
    } finally {
      setIsCreatingProject(false)
    }
  }

  // 버전 선택 토글 (Diff 비교용) - 'v0' 또는 versionId
  const handleToggleVersion = (id) => {
    setSelectedVersions(prev => {
      if (prev.includes(id)) {
        return prev.filter(selected => selected !== id)
      } else {
        if (prev.length >= 2) {
          toast.error('최대 2개 버전만 선택 가능합니다')
          return prev
        }
        return [...prev, id]
      }
    })
  }

  // Diff 비교 실행
  const handleCompare = async () => {
    if (selectedVersions.length !== 2) {
      toast.error('2개의 버전을 선택해주세요')
      return
    }

    try {
      setIsLoadingDiff(true)

      // v0와 QA 버전의 데이터를 가져오기
      const getData = async (id) => {
        if (id === 'v0') {
          return {
            version_number: 0,
            corrected_script: originalScript,
            version_name: '원본 스크립트',
            created_at: null
          }
        } else {
          const { data } = await projectApi.getQAVersion(projectId, id)
          return data
        }
      }

      const [data1, data2] = await Promise.all([
        getData(selectedVersions[0]),
        getData(selectedVersions[1])
      ])

      // 버전 번호 기준으로 old/new 정렬
      const [oldData, newData] = data1.version_number < data2.version_number
        ? [data1, data2]
        : [data2, data1]

      setDiffData({ old: oldData, new: newData })
      logger.info('Diff comparison loaded', {
        oldVersion: oldData.version_number,
        newVersion: newData.version_number
      })

    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      toast.error(`비교 데이터 로드 실패: ${message}`)
      logger.error('Failed to load diff data', { error: message })
    } finally {
      setIsLoadingDiff(false)
    }
  }

  // Diff 닫기
  const handleCloseDiff = () => {
    setDiffData(null)
    setSelectedVersions([])
    setComparisonMode(false)
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
      {/* 헤더: 버전 비교 토글 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-200">버전 목록</h3>
        <button
          onClick={() => {
            setComparisonMode(!comparisonMode)
            if (comparisonMode) {
              setSelectedVersions([])
              setDiffData(null)
            }
          }}
          className="flex items-center gap-2 px-3 py-1.5 bg-dark-card border border-dark-border rounded hover:bg-dark-hover transition-colors text-sm"
        >
          <GitCompare className="w-4 h-4" />
          <span>{comparisonMode ? '비교 취소' : '버전 비교'}</span>
        </button>
      </div>

      {/* v0 (원본 스크립트) - 비교 모드일 때만 표시 */}
      {comparisonMode && originalScript && (
        <div className="p-4 bg-dark-card border border-primary/30 rounded-lg">
          <div className="flex gap-3">
            <div className="flex-shrink-0 pt-0.5">
              <input
                type="checkbox"
                checked={selectedVersions.includes('v0')}
                onChange={() => handleToggleVersion('v0')}
                disabled={
                  !selectedVersions.includes('v0') &&
                  selectedVersions.length >= 2
                }
                className="w-4 h-4 rounded border-dark-border bg-dark-bg text-primary focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-semibold text-gray-200">v0</span>
                <span className="text-sm text-gray-300">원본 스크립트</span>
                <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded">
                  초기
                </span>
              </div>
              <div className="text-xs text-gray-500">
                QA 검증 이전의 원본 스크립트
              </div>
            </div>
          </div>
        </div>
      )}

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
            <div className="flex gap-3">
              {/* 체크박스 (비교 모드일 때만 표시) */}
              {comparisonMode && (
                <div className="flex-shrink-0 pt-0.5">
                  <input
                    type="checkbox"
                    checked={selectedVersions.includes(version.id)}
                    onChange={() => handleToggleVersion(version.id)}
                    disabled={
                      !selectedVersions.includes(version.id) &&
                      selectedVersions.length >= 2
                    }
                    className="w-4 h-4 rounded border-dark-border bg-dark-bg text-primary focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              )}

              <div className="flex-1 min-w-0">
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
                  <div className="text-xs text-gray-500 space-y-0.5">
                    <div>
                      {new Date(version.created_at).toLocaleString('ko-KR')} | {version.model}
                    </div>
                    {(version.input_tokens || version.output_tokens) && (
                      <div>
                        입력: {version.input_tokens?.toLocaleString() || 'N/A'} |
                        출력: {version.output_tokens?.toLocaleString() || 'N/A'}
                      </div>
                    )}
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
            </div>
          )}
        </div>
      ))}

      {/* 비교하기 버튼 (2개 선택 시) */}
      {comparisonMode && selectedVersions.length === 2 && (
        <div className="flex justify-center mt-4">
          <button
            onClick={handleCompare}
            disabled={isLoadingDiff}
            className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors disabled:opacity-50 font-medium"
          >
            {isLoadingDiff ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <GitCompare className="w-4 h-4" />
            )}
            <span>비교하기</span>
          </button>
        </div>
      )}

      {/* Diff 뷰어 */}
      {diffData && (
        <div className="mt-6 pt-6 border-t border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-gray-200">
              v{diffData.old.version_number}{diffData.old.version_name ? ` (${diffData.old.version_name})` : ''}
              {' vs '}
              v{diffData.new.version_number}{diffData.new.version_name ? ` (${diffData.new.version_name})` : ''}
            </h3>
            <button
              onClick={handleCloseDiff}
              className="px-3 py-1.5 bg-dark-card border border-dark-border rounded hover:bg-dark-hover transition-colors text-sm"
            >
              닫기
            </button>
          </div>

          <ReactDiffViewer
            oldValue={diffData.old.corrected_script}
            newValue={diffData.new.corrected_script}
            splitView={!isMobile}
            showDiffOnly={false}
            useDarkTheme={true}
            styles={{
              variables: {
                dark: {
                  diffViewerBackground: '#1a1b26',
                  diffViewerColor: '#e2e8f0',
                  addedBackground: '#10b98114',
                  addedColor: '#34d399',
                  removedBackground: '#ef444414',
                  removedColor: '#f87171',
                  wordAddedBackground: '#10b98128',
                  wordRemovedBackground: '#ef444428',
                  addedGutterBackground: '#10b98120',
                  removedGutterBackground: '#ef444420',
                  gutterBackground: '#0f111a',
                  gutterBackgroundDark: '#0f111a',
                  highlightBackground: '#374151',
                  highlightGutterBackground: '#374151',
                },
              },
              line: {
                padding: '8px 2px',
                fontSize: '14px',
              },
            }}
          />
        </div>
      )}

      {/* 선택된 버전 상세 보기 */}
      {selectedVersion && (
        <div className="mt-6 pt-6 border-t border-dark-border">
          <div className="flex items-center justify-between gap-2 mb-2">
            <h3 className="text-sm sm:text-base font-semibold text-gray-200 min-w-0 truncate">
              v{selectedVersion.version_number} 스크립트
            </h3>
            <div className="flex gap-1.5 sm:gap-2 flex-shrink-0">
              <button
                onClick={() => handleCopyScript(selectedVersion.corrected_script)}
                className="flex items-center gap-1 px-2 sm:px-3 py-1.5 bg-dark-card border border-dark-border rounded hover:bg-dark-hover transition-colors text-sm whitespace-nowrap"
              >
                <Copy className="w-3 h-3" />
                <span className="hidden xs:inline">복사</span>
              </button>
              <button
                onClick={() => handleCreateProjectFromVersion(selectedVersion)}
                disabled={isCreatingProject}
                className="flex items-center gap-1 px-2 sm:px-3 py-1.5 bg-primary/10 border border-primary/30 text-primary rounded hover:bg-primary/20 transition-colors disabled:opacity-50 text-sm font-medium whitespace-nowrap"
              >
                {isCreatingProject ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <FilePlus className="w-3 h-3" />
                )}
                <span className="hidden xs:inline">프로젝트 생성</span>
                <span className="xs:hidden">생성</span>
              </button>
              <button
                onClick={() => setSelectedVersion(null)}
                className="px-2 sm:px-3 py-1.5 bg-dark-card border border-dark-border rounded hover:bg-dark-hover transition-colors text-sm whitespace-nowrap"
              >
                닫기
              </button>
            </div>
          </div>
          {/* 메타 정보 */}
          <div className="text-xs text-gray-500 mb-4 space-y-0.5">
            <div>
              {new Date(selectedVersion.created_at).toLocaleString('ko-KR')} | {selectedVersion.model}
            </div>
            {(selectedVersion.input_tokens || selectedVersion.output_tokens) && (
              <div>
                입력 토큰: {selectedVersion.input_tokens?.toLocaleString() || 'N/A'} |
                출력 토큰: {selectedVersion.output_tokens?.toLocaleString() || 'N/A'}
              </div>
            )}
          </div>
          <pre className="bg-dark-bg p-4 rounded-lg border border-dark-border overflow-x-auto text-sm text-gray-200 whitespace-pre-wrap break-words">
            {selectedVersion.corrected_script}
          </pre>
        </div>
      )}
    </div>
  )
}

export default QAResultView
