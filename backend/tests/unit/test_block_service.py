"""
BlockService 단위 테스트
"""

import pytest
from app.services.block_service import BlockService
from app.models import Block, Project
from app.models.block import BlockStatus
from app.errors import BlockNotFoundError, BlockSplitError, BlockMergeError


@pytest.fixture
def block_service():
    return BlockService()


@pytest.fixture
def project(db_session):
    """테스트용 프로젝트"""
    project = Project(
        title="테스트 프로젝트",
        script_raw="테스트"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def project_with_blocks(db_session, project):
    """테스트용 프로젝트와 블록들"""
    blocks = []
    for i in range(3):
        block = Block(
            project_id=project.id,
            index=i,
            text=f"블록 {i+1}의 텍스트 내용입니다. 충분히 긴 텍스트입니다.",
            keywords=[f"키워드{i+1}A", f"키워드{i+1}B"],
            status=BlockStatus.DRAFT
        )
        db_session.add(block)
        db_session.commit()
        db_session.refresh(block)
        blocks.append(block)

    return project, blocks


class TestGetBlock:
    """get_block 테스트"""

    def test_get_existing_block(self, db_session, block_service, project_with_blocks):
        """존재하는 블록 조회"""
        project, blocks = project_with_blocks
        block = block_service.get_block(db_session, blocks[0].id)

        assert block.id == blocks[0].id
        assert block.text == blocks[0].text

    def test_get_nonexistent_block_raises_error(self, db_session, block_service):
        """존재하지 않는 블록 조회 시 에러"""
        with pytest.raises(BlockNotFoundError):
            block_service.get_block(db_session, "non-existent-id")


class TestCreateBlock:
    """create_block 테스트"""

    def test_create_block_at_beginning(self, db_session, block_service, project_with_blocks):
        """시작 위치에 블록 추가"""
        project, blocks = project_with_blocks

        new_block = block_service.create_block(
            db_session,
            project.id,
            text="새 블록",
            keywords=["새키워드"],
            insert_at=0
        )

        assert new_block.index == 0
        assert new_block.text == "새 블록"

        # 기존 블록들 인덱스 확인
        all_blocks = block_service.get_project_blocks(db_session, project.id)
        assert len(all_blocks) == 4
        assert [b.index for b in all_blocks] == [0, 1, 2, 3]

    def test_create_block_in_middle(self, db_session, block_service, project_with_blocks):
        """중간 위치에 블록 추가"""
        project, blocks = project_with_blocks

        new_block = block_service.create_block(
            db_session,
            project.id,
            text="중간 블록",
            insert_at=1
        )

        assert new_block.index == 1

        all_blocks = block_service.get_project_blocks(db_session, project.id)
        assert len(all_blocks) == 4


class TestUpdateBlock:
    """update_block 테스트"""

    def test_update_text(self, db_session, block_service, project_with_blocks):
        """텍스트 수정"""
        project, blocks = project_with_blocks
        block = blocks[0]

        updated = block_service.update_block(
            db_session, block.id, text="수정된 텍스트"
        )

        assert updated.text == "수정된 텍스트"
        assert updated.status == BlockStatus.DRAFT

    def test_update_keywords(self, db_session, block_service, project_with_blocks):
        """키워드 수정"""
        project, blocks = project_with_blocks
        block = blocks[0]

        updated = block_service.update_block(
            db_session, block.id, keywords=["새키워드1", "새키워드2"]
        )

        assert updated.keywords == ["새키워드1", "새키워드2"]


class TestDeleteBlock:
    """delete_block 테스트"""

    def test_delete_middle_block(self, db_session, block_service, project_with_blocks):
        """중간 블록 삭제"""
        project, blocks = project_with_blocks
        middle_block_id = blocks[1].id

        block_service.delete_block(db_session, middle_block_id)

        remaining = block_service.get_project_blocks(db_session, project.id)
        assert len(remaining) == 2
        assert [b.index for b in remaining] == [0, 1]

    def test_delete_nonexistent_block_raises_error(self, db_session, block_service):
        """존재하지 않는 블록 삭제 시 에러"""
        with pytest.raises(BlockNotFoundError):
            block_service.delete_block(db_session, "non-existent-id")


class TestSplitBlock:
    """split_block 테스트"""

    def test_split_block_success(self, db_session, block_service, project_with_blocks):
        """블록 분할 성공"""
        project, blocks = project_with_blocks
        block = blocks[0]
        original_text = block.text
        split_pos = len(original_text) // 2

        first, second = block_service.split_block(db_session, block.id, split_pos)

        assert first.text == original_text[:split_pos].strip()
        assert second.text == original_text[split_pos:].strip()
        assert first.status == BlockStatus.DRAFT
        assert second.status == BlockStatus.DRAFT

    def test_split_at_invalid_position_raises_error(self, db_session, block_service, project_with_blocks):
        """유효하지 않은 위치에서 분할 시 에러"""
        project, blocks = project_with_blocks
        block = blocks[0]

        # 텍스트 끝에서 분할 시도
        with pytest.raises(BlockSplitError):
            block_service.split_block(db_session, block.id, len(block.text))

    def test_split_updates_subsequent_indices(self, db_session, block_service, project_with_blocks):
        """분할 후 후속 블록 인덱스 업데이트"""
        project, blocks = project_with_blocks
        block = blocks[0]
        split_pos = 10

        first, second = block_service.split_block(db_session, block.id, split_pos)

        all_blocks = block_service.get_project_blocks(db_session, project.id)
        indices = [b.index for b in all_blocks]
        assert indices == [0, 1, 2, 3]  # 4개 블록, 0-3 인덱스


class TestMergeBlocks:
    """merge_blocks 테스트"""

    def test_merge_two_blocks(self, db_session, block_service, project_with_blocks):
        """두 블록 합치기"""
        project, blocks = project_with_blocks

        merged = block_service.merge_blocks(
            db_session,
            project.id,
            [blocks[0].id, blocks[1].id]
        )

        assert "블록 1" in merged.text
        assert "블록 2" in merged.text
        assert merged.status == BlockStatus.DRAFT

        remaining = block_service.get_project_blocks(db_session, project.id)
        assert len(remaining) == 2

    def test_merge_keywords_combined(self, db_session, block_service, project_with_blocks):
        """합치기 시 키워드 합침"""
        project, blocks = project_with_blocks

        merged = block_service.merge_blocks(
            db_session,
            project.id,
            [blocks[0].id, blocks[1].id]
        )

        # 중복 제거된 키워드
        assert "키워드1A" in merged.keywords
        assert "키워드2A" in merged.keywords

    def test_merge_non_adjacent_raises_error(self, db_session, block_service, project_with_blocks):
        """인접하지 않은 블록 합치기 시 에러"""
        project, blocks = project_with_blocks

        with pytest.raises(BlockMergeError) as exc_info:
            block_service.merge_blocks(
                db_session,
                project.id,
                [blocks[0].id, blocks[2].id]
            )

        assert "인접한 블록만" in str(exc_info.value.message)

    def test_merge_not_found_raises_error(self, db_session, block_service, project_with_blocks):
        """존재하지 않는 블록 포함 시 에러"""
        project, blocks = project_with_blocks

        with pytest.raises(BlockMergeError) as exc_info:
            block_service.merge_blocks(
                db_session,
                project.id,
                [blocks[0].id, "non-existent-id"]
            )

        assert "찾을 수 없습니다" in str(exc_info.value.message)


class TestReindexBlocks:
    """reindex_blocks 테스트"""

    def test_reindex_after_gap(self, db_session, block_service, project_with_blocks):
        """인덱스 갭 발생 후 재정렬"""
        project, blocks = project_with_blocks

        # 인덱스 갭 발생 시킴 (직접 조작)
        blocks[0].index = 0
        blocks[1].index = 5
        blocks[2].index = 10
        db_session.commit()

        reindexed = block_service.reindex_blocks(db_session, project.id)

        assert [b.index for b in reindexed] == [0, 1, 2]
