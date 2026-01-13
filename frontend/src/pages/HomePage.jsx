import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, Info } from 'lucide-react'
import toast from 'react-hot-toast'

import ScriptEditor from '../components/script/ScriptEditor'
import Button from '../components/common/Button'
import { LoadingOverlay } from '../components/common/Loading'
import ErrorAlert from '../components/common/ErrorAlert'
import { projectApi } from '../services/api'
import logger from '../utils/logger'

function HomePage() {
  const navigate = useNavigate()
  const [script, setScript] = useState('')
  const [title, setTitle] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState(null)

  const handleGenerate = async () => {
    if (!script.trim()) {
      toast.error('Please enter your script first')
      return
    }

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

      // 2. Generate 실행
      toast.loading('Generating visuals...', { id: 'generate' })

      await projectApi.generate(projectId)

      toast.success('Visuals generated successfully!', { id: 'generate' })
      logger.info('Generate completed', { projectId })

      // 3. 결과 페이지로 이동
      navigate(`/project/${projectId}`)

    } catch (err) {
      logger.error('Generate failed', err)
      const errorMessage = err.response?.data?.detail?.message || err.message || 'Failed to generate visuals'
      setError(errorMessage)
      toast.error(errorMessage, { id: 'generate' })
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="flex-1 p-4 md:p-6">
      {isGenerating && (
        <LoadingOverlay message="Splitting script and matching visuals..." />
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

              {/* Generate 버튼 */}
              <Button
                onClick={handleGenerate}
                loading={isGenerating}
                disabled={!script.trim()}
                icon={Sparkles}
                className="w-full"
                size="lg"
              >
                Generate Visuals
              </Button>

              <p className="text-xs text-gray-500 text-center mt-2">
                Estimated time: 2-4 minutes
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
