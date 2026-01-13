import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, Info, X, FileText } from 'lucide-react'
import toast from 'react-hot-toast'

import ScriptEditor from '../components/script/ScriptEditor'
import Button from '../components/common/Button'
import { LoadingOverlay } from '../components/common/Loading'
import ErrorAlert from '../components/common/ErrorAlert'
import { projectApi } from '../services/api'
import logger from '../utils/logger'

// 로딩 단계별 메시지
const LOADING_STEPS = [
  '스크립트 분석중...',
  '이미지 찾는 중...'
]

const ANALYZE_STEPS = [
  '스크립트 분석중...',
  '블록 생성 중...'
]

function HomePage() {
  const navigate = useNavigate()
  const [script, setScript] = useState('')
  const [title, setTitle] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [error, setError] = useState(null)
  const abortControllerRef = useRef(null)
  const loadingTimerRef = useRef(null)

  const isLoading = isGenerating || isAnalyzing

  // 로딩 단계 자동 전환
  useEffect(() => {
    if (isLoading) {
      setLoadingStep(0)
      // 5초 후 두 번째 단계로 전환
      loadingTimerRef.current = setTimeout(() => {
        setLoadingStep(1)
      }, 5000)
    } else {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current)
        loadingTimerRef.current = null
      }
      setLoadingStep(0)
    }

    return () => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current)
      }
    }
  }, [isLoading])

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      toast.dismiss('generate')
      toast.dismiss('analyze')
      toast('Cancelled', { icon: 'X' })
      setIsGenerating(false)
      setIsAnalyzing(false)
    }
  }

  // Analyze Script (2단계 워크플로우 - Step 1)
  const handleAnalyze = async () => {
    if (!script.trim()) {
      toast.error('Please enter your script first')
      return
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    setIsAnalyzing(true)
    setError(null)

    try {
      logger.info('Starting script analysis', { scriptLength: script.length })

      // 1. 프로젝트 생성
      const createResponse = await projectApi.create({
        script_raw: script,
        title: title || undefined
      })

      const projectId = createResponse.data.id
      logger.info('Project created', { projectId })

      // 2. Split 실행 (분할만, 매칭 없이)
      toast.loading('Analyzing script...', { id: 'analyze' })

      await projectApi.split(projectId, {
        signal: abortControllerRef.current.signal
      })

      toast.success('Analysis completed!', { id: 'analyze' })
      logger.info('Split completed', { projectId })

      // 3. 편집 페이지로 이동
      navigate(`/project/${projectId}/edit`)

    } catch (err) {
      if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
        logger.info('Analysis cancelled by user')
        return
      }

      logger.error('Analysis failed', err)

      let errorMessage = 'Failed to analyze script'
      if (err.response?.data?.detail?.message) {
        errorMessage = err.response.data.detail.message
      } else if (err.message) {
        errorMessage = err.message
      }

      setError(errorMessage)
      toast.error(errorMessage, { id: 'analyze' })
    } finally {
      setIsAnalyzing(false)
      abortControllerRef.current = null
    }
  }

  const handleGenerate = async () => {
    if (!script.trim()) {
      toast.error('Please enter your script first')
      return
    }

    // 이전 요청 취소
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    setIsGenerating(true)
    setError(null)

    try {
      logger.info('Starting project creation', { scriptLength: script.length })

      // 1. 프로젝트 생성
      const createResponse = await projectApi.create({
        script_raw: script,
        title: title || undefined
      })

      const projectId = createResponse.data.id
      logger.info('Project created', { projectId })

      // 2. Generate 실행 (AbortController 전달)
      toast.loading('Generating...', { id: 'generate' })

      await projectApi.generate(projectId, {
        signal: abortControllerRef.current.signal
      })

      toast.success('Visuals generated successfully!', { id: 'generate' })
      logger.info('Generate completed', { projectId })

      // 3. 결과 페이지로 이동
      navigate(`/project/${projectId}`)

    } catch (err) {
      // 취소된 요청은 무시
      if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
        logger.info('Generate cancelled by user')
        return
      }

      logger.error('Generate failed', err)

      // 에러 메시지 파싱
      let errorMessage = 'Failed to generate visuals'
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        errorMessage = 'Request timed out. Please try again with a shorter script.'
      } else if (err.response?.data?.detail?.message) {
        errorMessage = err.response.data.detail.message
      } else if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string'
          ? err.response.data.detail
          : JSON.stringify(err.response.data.detail)
      } else if (err.message) {
        errorMessage = err.message
      }

      setError(errorMessage)
      toast.error(errorMessage, { id: 'generate' })
    } finally {
      setIsGenerating(false)
      abortControllerRef.current = null
    }
  }

  return (
    <div className="flex-1 p-4 md:p-6">
      {isLoading && (
        <LoadingOverlay
          message={isAnalyzing ? ANALYZE_STEPS[loadingStep] : LOADING_STEPS[loadingStep]}
          onCancel={handleCancel}
        />
      )}

      <div className="max-w-5xl mx-auto">
        {/* 페이지 헤더 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white mb-1">Script Editor</h1>
          <p className="text-gray-400 text-sm">Transform your narrative into visual sequences instantly.</p>
        </div>

        {/* 에러 표시 */}
        {error && (
          <div className="mb-4">
            <ErrorAlert error={error} onClose={() => setError(null)} />
          </div>
        )}

        <div className="flex flex-col lg:flex-row gap-6">
          {/* 왼쪽: 스크립트 에디터 */}
          <div className="flex-1">
            {/* 프로젝트 제목 (선택) */}
            <div className="mb-4">
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Project title (optional)"
                className="w-full bg-dark-card border border-dark-border rounded-lg px-4 py-2 text-white placeholder-gray-500 outline-none focus:border-primary"
              />
            </div>

            {/* 스크립트 편집기 */}
            <ScriptEditor
              value={script}
              onChange={setScript}
              disabled={isGenerating}
              placeholder="Paste your YouTube script here or start typing your masterpiece..."
            />
          </div>

          {/* 오른쪽: Visual Mapping 옵션 */}
          <div className="lg:w-72">
            <div className="bg-dark-card border border-dark-border rounded-lg p-4 sticky top-4">
              <h3 className="text-sm font-medium text-white mb-4">VISUAL MAPPING</h3>

              {/* Video Style */}
              <div className="mb-4">
                <label className="text-xs text-gray-400 mb-1 block">Video Style</label>
                <select className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-primary">
                  <option value="cinematic">Cinematic Narrative</option>
                  <option value="documentary">Documentary</option>
                  <option value="minimal">Minimal</option>
                </select>
              </div>

              {/* Aspect Ratio */}
              <div className="mb-6">
                <label className="text-xs text-gray-400 mb-2 block">Aspect Ratio</label>
                <div className="flex gap-2">
                  {['16:9', '9:16', '1:1'].map((ratio) => (
                    <button
                      key={ratio}
                      className={`flex-1 py-1.5 text-xs rounded-lg border ${
                        ratio === '16:9'
                          ? 'bg-primary border-primary text-white'
                          : 'border-dark-border text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      {ratio}
                    </button>
                  ))}
                </div>
              </div>

              {/* Analyze Script 버튼 (2단계 워크플로우) */}
              <Button
                onClick={handleAnalyze}
                loading={isAnalyzing}
                disabled={!script.trim() || isGenerating}
                icon={FileText}
                className="w-full"
                size="lg"
              >
                Analyze Script
              </Button>

              <p className="text-xs text-gray-500 text-center mt-2 mb-3">
                Edit blocks before generating
              </p>

              {/* Quick Generate 버튼 */}
              <Button
                onClick={handleGenerate}
                loading={isGenerating}
                disabled={!script.trim() || isAnalyzing}
                icon={Sparkles}
                variant="outline"
                className="w-full"
                size="md"
              >
                Quick Generate
              </Button>

              <p className="text-xs text-gray-500 text-center mt-2">
                Skip editing (2-4 min)
              </p>

              {/* Pro Tip */}
              <div className="mt-6 p-3 bg-dark-bg rounded-lg">
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-medium text-white mb-1">Pro Tip</p>
                    <p className="text-xs text-gray-400">
                      Use brackets like [Show Map] to suggest specific scenes to the AI engine.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage
