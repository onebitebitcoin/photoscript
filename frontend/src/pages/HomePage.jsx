import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FileText, Trash2, Loader2, ChevronRight, X } from 'lucide-react'
import toast from 'react-hot-toast'

import ScriptEditor from '../components/script/ScriptEditor'
import Button from '../components/common/Button'
import { LoadingOverlay } from '../components/common/Loading'
import ErrorAlert from '../components/common/ErrorAlert'
import { projectApi } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import logger from '../utils/logger'

function HomePage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [projects, setProjects] = useState([])
  const [isLoadingProjects, setIsLoadingProjects] = useState(true)
  const [showNewScript, setShowNewScript] = useState(false)
  const [script, setScript] = useState('')
  const [title, setTitle] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [error, setError] = useState(null)
  const abortControllerRef = useRef(null)

  // 프로젝트 목록 로드
  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      setIsLoadingProjects(true)
      const { data } = await projectApi.list()
      setProjects(data)
      logger.info('Projects loaded', { count: data.length })
    } catch (err) {
      logger.error('Failed to load projects', err)
      toast.error('프로젝트 목록을 불러오는데 실패했습니다')
    } finally {
      setIsLoadingProjects(false)
    }
  }

  // 새 스크립트 생성 및 분석
  const handleCreateScript = async () => {
    if (!script.trim()) {
      toast.error('스크립트를 입력해주세요')
      return
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    setIsCreating(true)
    setError(null)

    try {
      logger.info('Creating new script', { scriptLength: script.length })

      // 1. 프로젝트 생성
      const createResponse = await projectApi.create({
        script_raw: script,
        title: title || undefined
      })

      const projectId = createResponse.data.id
      logger.info('Project created', { projectId })

      // 2. Split 실행
      toast.loading('스크립트 분석 중...', { id: 'create' })

      await projectApi.split(projectId, {
        signal: abortControllerRef.current.signal
      })

      toast.success('스크립트 분석 완료!', { id: 'create' })
      logger.info('Split completed', { projectId })

      // 3. 편집 페이지로 이동
      navigate(`/project/${projectId}/edit`)

    } catch (err) {
      if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
        logger.info('Create cancelled by user')
        return
      }

      logger.error('Create failed', err)
      const errorMessage = err.response?.data?.detail?.message || err.message || '스크립트 생성에 실패했습니다'
      setError(errorMessage)
      toast.error(errorMessage, { id: 'create' })
    } finally {
      setIsCreating(false)
      abortControllerRef.current = null
    }
  }

  // 프로젝트 삭제
  const handleDelete = async (projectId, e) => {
    e.stopPropagation()

    if (!confirm('정말 삭제하시겠습니까?')) return

    setDeletingId(projectId)
    try {
      await projectApi.delete(projectId)
      setProjects(prev => prev.filter(p => p.id !== projectId))
      toast.success('삭제되었습니다')
      logger.info('Project deleted', { projectId })
    } catch (err) {
      logger.error('Failed to delete project', err)
      toast.error('삭제에 실패했습니다')
    } finally {
      setDeletingId(null)
    }
  }

  // 프로젝트 클릭 - 편집 페이지로 이동
  const handleProjectClick = (projectId) => {
    navigate(`/project/${projectId}/edit`)
  }

  // 날짜 포맷
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <div className="min-h-screen bg-dark-bg overflow-x-hidden">
      {isCreating && (
        <LoadingOverlay
          message="스크립트 분석 중..."
          onCancel={() => {
            if (abortControllerRef.current) {
              abortControllerRef.current.abort()
              setIsCreating(false)
            }
          }}
        />
      )}

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* 헤더 */}
        <div className="flex items-center gap-2 sm:gap-3 mb-8">
          <h1 className="text-xl sm:text-2xl font-bold text-white">Dashboard</h1>
          {user && (
            <span className="text-sm text-gray-400 hidden sm:inline">{user.nickname}</span>
          )}
        </div>

        {/* 에러 표시 */}
        {error && (
          <div className="mb-6">
            <ErrorAlert error={error} onClose={() => setError(null)} />
          </div>
        )}

        {/* 프로젝트 목록 */}
        <div>
          <h2 className="text-lg font-medium text-white mb-4">
            저장된 스크립트 ({projects.length})
          </h2>

          {isLoadingProjects ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="space-y-2">
              {/* 새 스크립트 추가 카드 */}
              {!showNewScript ? (
                <div
                  onClick={() => setShowNewScript(true)}
                  className="bg-dark-card border border-dashed border-primary/50 rounded-lg p-4 hover:border-primary hover:bg-primary/5 cursor-pointer transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary/20 rounded-lg flex items-center justify-center group-hover:bg-primary/30 transition-colors">
                      <Plus className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="text-white font-medium">새 스크립트 작성</h3>
                      <p className="text-sm text-gray-400 mt-0.5">유튜브 스크립트를 추가하세요</p>
                    </div>
                  </div>
                </div>
              ) : (
                /* 새 스크립트 작성 폼 */
                <div className="bg-dark-card border border-primary/50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-medium text-white">새 스크립트 작성</h2>
                    <button
                      onClick={() => setShowNewScript(false)}
                      className="p-1.5 text-gray-400 hover:text-white hover:bg-dark-hover rounded transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* 제목 */}
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="프로젝트 제목 (선택사항)"
                    className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 mb-4 text-white placeholder-gray-500 outline-none focus:border-primary"
                  />

                  {/* 스크립트 편집기 */}
                  <ScriptEditor
                    value={script}
                    onChange={setScript}
                    disabled={isCreating}
                    placeholder="유튜브 스크립트를 붙여넣거나 직접 작성하세요..."
                  />

                  {/* 생성 버튼 */}
                  <div className="mt-4 flex justify-end">
                    <Button
                      onClick={handleCreateScript}
                      loading={isCreating}
                      disabled={!script.trim()}
                      icon={FileText}
                    >
                      스크립트 분석
                    </Button>
                  </div>
                </div>
              )}

              {/* 기존 프로젝트 목록 */}
              {projects.length === 0 && !showNewScript ? (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>아직 저장된 스크립트가 없습니다</p>
                  <p className="text-sm mt-1">위의 카드를 클릭하여 새 스크립트를 작성해보세요</p>
                </div>
              ) : (
                projects.map((project) => (
                  <div
                    key={project.id}
                    onClick={() => handleProjectClick(project.id)}
                    className="bg-dark-card border border-dark-border rounded-lg p-4 hover:border-primary/50 cursor-pointer transition-colors group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-white font-medium truncate">
                          {project.title || '제목 없음'}
                        </h3>
                        <p className="text-sm text-gray-500 mt-1">
                          {formatDate(project.created_at)}
                        </p>
                      </div>

                      <div className="flex items-center gap-2 ml-4">
                        <button
                          onClick={(e) => handleDelete(project.id, e)}
                          disabled={deletingId === project.id}
                          className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                        >
                          {deletingId === project.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </button>
                        <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-primary transition-colors" />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default HomePage
