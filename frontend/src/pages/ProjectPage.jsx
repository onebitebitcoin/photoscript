import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Share2, Download, Plus } from 'lucide-react'

import BlockList from '../components/script/BlockList'
import VisualPanel from '../components/visual/VisualPanel'
import Button from '../components/common/Button'
import Loading from '../components/common/Loading'
import ErrorAlert from '../components/common/ErrorAlert'
import { useProject } from '../hooks/useProject'

function ProjectPage() {
  const { projectId } = useParams()
  const { project, blocks, isLoading, error, refetch } = useProject(projectId)
  const [selectedBlockId, setSelectedBlockId] = useState(null)

  // 첫 번째 블록 자동 선택
  if (blocks.length > 0 && !selectedBlockId) {
    setSelectedBlockId(blocks[0].id)
  }

  // 로딩 중
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loading size="lg" message="Loading project..." />
      </div>
    )
  }

  // 에러
  if (error) {
    return (
      <div className="flex-1 p-6">
        <ErrorAlert error={error} />
        <div className="mt-4">
          <Link to="/" className="text-primary hover:underline">
            Back to home
          </Link>
        </div>
      </div>
    )
  }

  // 프로젝트 없음
  if (!project) {
    return (
      <div className="flex-1 p-6 text-center text-gray-500">
        <p>Project not found</p>
        <Link to="/" className="text-primary hover:underline mt-2 inline-block">
          Back to home
        </Link>
      </div>
    )
  }

  const matchedCount = blocks.filter(b => b.status === 'MATCHED' || b.status === 'CUSTOM').length
  const totalCount = blocks.length

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* 상단 바 */}
      <div className="bg-dark-card border-b border-dark-border px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="p-1.5 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-white font-medium">
              {project.title || 'Untitled Project'}
            </h1>
            <p className="text-xs text-gray-500">
              {matchedCount}/{totalCount} segments matched
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" icon={Share2}>
            Share
          </Button>
          <Button variant="ghost" size="sm" icon={Download}>
            Export
          </Button>
        </div>
      </div>

      {/* 메인 콘텐츠 - 2열 분할 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 좌측: 블록 리스트 */}
        <div className="w-full md:w-1/2 lg:w-2/5 border-r border-dark-border overflow-y-auto p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-gray-400 uppercase">
              Segments ({blocks.length})
            </h2>
            <Button variant="outline" size="sm" icon={Plus}>
              Add Block
            </Button>
          </div>

          <BlockList
            blocks={blocks}
            selectedId={selectedBlockId}
            onSelect={setSelectedBlockId}
            isLoading={false}
          />
        </div>

        {/* 우측: 비주얼 패널 */}
        <div className="hidden md:block md:w-1/2 lg:w-3/5 overflow-y-auto bg-dark-bg">
          <VisualPanel
            blockId={selectedBlockId}
            onAssetChange={refetch}
          />
        </div>
      </div>

      {/* 모바일: 선택된 블록의 비주얼 표시 (하단 시트로 구현 가능) */}
      {selectedBlockId && (
        <div className="md:hidden fixed bottom-0 left-0 right-0 bg-dark-card border-t border-dark-border p-4">
          <button
            onClick={() => {/* 모바일 비주얼 패널 열기 */}}
            className="w-full py-3 bg-primary text-white rounded-lg"
          >
            View Visuals
          </button>
        </div>
      )}
    </div>
  )
}

export default ProjectPage
