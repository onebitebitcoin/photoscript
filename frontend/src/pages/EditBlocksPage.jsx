import { useState, useEffect, useCallback, Fragment } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Merge, Sparkles, Loader2, AlertCircle } from 'lucide-react'
import { projectApi, blockApi } from '../services/api'
import EditableBlockCard from '../components/script/EditableBlockCard'
import AddBlockButton from '../components/script/AddBlockButton'
import Button from '../components/common/Button'
import logger from '../utils/logger'
import toast from 'react-hot-toast'

/**
 * 블록 편집 페이지
 * 스크립트 분할 후 사용자가 블록을 편집하고 컨펌하는 페이지
 */
function EditBlocksPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [project, setProject] = useState(null)
  const [blocks, setBlocks] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isMatching, setIsMatching] = useState(false)
  const [isMerging, setIsMerging] = useState(false)
  const [isAddingBlock, setIsAddingBlock] = useState(false)
  const [newBlockId, setNewBlockId] = useState(null) // 새로 추가된 블록 ID (자동 편집 모드용)
  const [error, setError] = useState(null)

  // 프로젝트 및 블록 로드
  const loadProject = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const { data } = await projectApi.get(projectId)
      setProject(data)
      setBlocks(data.blocks || [])

      logger.info('Project loaded', { projectId, blocksCount: data.blocks?.length })
    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      setError(message)
      logger.error('Failed to load project', { projectId, error: message })
    } finally {
      setIsLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    loadProject()
  }, [loadProject])

  // 블록 선택 토글
  const handleSelect = (blockId) => {
    setSelectedIds(prev =>
      prev.includes(blockId)
        ? prev.filter(id => id !== blockId)
        : [...prev, blockId]
    )
  }

  // 블록 업데이트
  const handleUpdateBlock = async (blockId, data) => {
    try {
      const { data: updatedBlock } = await blockApi.update(blockId, data)
      setBlocks(prev =>
        prev.map(b => b.id === blockId ? { ...b, ...updatedBlock } : b)
      )
      logger.info('Block updated', { blockId })
      toast.success('Block updated')
    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      logger.error('Failed to update block', { blockId, error: message })
      throw err
    }
  }

  // 블록 변경 시 프로젝트 다시 로드
  const handleBlockChange = async () => {
    await loadProject()
    toast.success('Visuals updated')
  }

  // 블록 합치기
  const handleMergeBlocks = async () => {
    if (selectedIds.length < 2) return

    // 인접한 블록인지 확인
    const selectedBlocks = blocks.filter(b => selectedIds.includes(b.id))
    const indices = selectedBlocks.map(b => b.index).sort((a, b) => a - b)

    for (let i = 0; i < indices.length - 1; i++) {
      if (indices[i + 1] - indices[i] !== 1) {
        setError('인접한 블록만 합칠 수 있습니다')
        return
      }
    }

    try {
      setIsMerging(true)
      setError(null)

      await projectApi.mergeBlocks(projectId, selectedIds)
      setSelectedIds([])
      await loadProject()

      logger.info('Blocks merged', { blockIds: selectedIds })
    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      setError(message)
      logger.error('Failed to merge blocks', { error: message })
    } finally {
      setIsMerging(false)
    }
  }

  // Generate Visuals (영상 우선 매칭)
  const handleGenerateVisuals = async () => {
    try {
      setIsMatching(true)
      setError(null)

      await projectApi.match(projectId, { video_priority: true })

      logger.info('Matching completed', { projectId })
      toast.success('비주얼 생성 완료!')

      // 홈으로 이동
      navigate('/')
    } catch (err) {
      const message = err.response?.data?.detail?.message || err.message
      setError(message)
      logger.error('Failed to match assets', { error: message })
    } finally {
      setIsMatching(false)
    }
  }

  // 새 블록 추가
  const handleAddBlock = async (insertAt) => {
    // 중복 요청 방지
    if (isAddingBlock) {
      logger.warn('Block add request blocked: already in progress')
      return
    }

    try {
      setIsAddingBlock(true)
      setError(null)

      logger.info('Adding block', { insertAt })

      const { data: newBlock } = await projectApi.createBlock(projectId, {
        text: '',
        keywords: [],
        insert_at: insertAt
      })

      // Backend 응답으로 전체 프로젝트 새로고침 (정확성 보장)
      await loadProject()

      // 새 블록 ID 저장 (자동 편집 모드)
      setNewBlockId(newBlock.id)

      logger.info('Block added', { blockId: newBlock.id, insertAt })
      toast.success('새 블록이 추가되었습니다')
    } catch (err) {
      // 에러 시 전체 새로고침으로 복구
      await loadProject()
      const message = err.response?.data?.detail?.message || err.message
      setError(message)
      logger.error('Failed to add block', { error: message })
      toast.error('블록 추가 실패')
    } finally {
      setIsAddingBlock(false)
    }
  }

  // 블록 삭제
  const handleDeleteBlock = async (blockId) => {
    try {
      setError(null)

      logger.info('Deleting block', { blockId })

      await blockApi.delete(blockId)

      // 선택 목록에서 제거
      setSelectedIds(prev => prev.filter(id => id !== blockId))

      // Backend 응답 후 전체 프로젝트 새로고침 (정확성 보장)
      await loadProject()

      logger.info('Block deleted', { blockId })
      toast.success('블록이 삭제되었습니다')
    } catch (err) {
      // 에러 시 전체 새로고침으로 복구
      await loadProject()
      const message = err.response?.data?.detail?.message || err.message
      setError(message)
      logger.error('Failed to delete block', { error: message })
      toast.error('블록 삭제 실패')
    }
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col bg-dark-bg">
      {/* 상단 바 */}
      <div className="bg-dark-card border-b border-dark-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="p-1.5 hover:bg-dark-hover rounded transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-400" />
            </button>
            <h1 className="text-lg font-semibold text-white truncate">
              {project?.title || '제목 없음'}
            </h1>
          </div>

          <div className="flex items-center gap-2">
            {selectedIds.length >= 2 && (
              <Button
                variant="outline"
                size="sm"
                disabled={isMerging}
                loading={isMerging}
                onClick={handleMergeBlocks}
                icon={Merge}
              >
                합치기
              </Button>
            )}
            <Button
              size="sm"
              loading={isMatching}
              onClick={handleGenerateVisuals}
              icon={Sparkles}
            >
              비주얼 생성
            </Button>
          </div>
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="mx-4 mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-400">{error}</p>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-400 hover:text-red-300"
          >
            <span className="sr-only">Close</span>
            &times;
          </button>
        </div>
      )}

      {/* 블록 목록 */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-3 max-w-3xl mx-auto">
          {/* 첫 번째 블록 위에 추가 버튼 */}
          <AddBlockButton
            onAdd={() => handleAddBlock(0)}
            isLoading={isAddingBlock}
          />

          {blocks.map((block) => (
            <Fragment key={block.id}>
              <EditableBlockCard
                block={block}
                isSelected={selectedIds.includes(block.id)}
                isNew={newBlockId === block.id}
                onSelect={handleSelect}
                onUpdate={handleUpdateBlock}
                onBlockChange={handleBlockChange}
                onNewBlockProcessed={() => setNewBlockId(null)}
                onDelete={handleDeleteBlock}
              />
              {/* 각 블록 아래에 추가 버튼 */}
              <AddBlockButton
                onAdd={() => handleAddBlock(block.index + 1)}
                isLoading={isAddingBlock}
              />
            </Fragment>
          ))}
        </div>
      </div>
    </div>
  )
}

export default EditBlocksPage
