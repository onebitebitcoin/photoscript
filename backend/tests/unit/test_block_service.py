"""
BlockService 단위 테스트 (Fractional Indexing 방식)
"""

import pytest
from app.services.block_service import BlockService
from app.models import Block, Project
from app.models.block import BlockStatus
from app.errors import BlockNotFoundError, BlockSplitError


@pytest.fixture
def block_service():
    return BlockService()


@pytest.fixture
def project(db_session, test_user):
    """테스트용 프로젝트"""
    project = Project(
        user_id=test_user.id,
        title="테스트 프로젝트",
        script_raw="테스트"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def project_with_blocks(db_session, project):
    """테스트용 프로젝트와 블록들 (Fractional Indexing)"""
    blocks = []
    for i in range(3):
        block = Block(
            project_id=project.id,
            order=float(i + 1),  # 1.0, 2.0, 3.0
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
    """create_block 테스트 (Fractional Indexing)"""

    def test_create_block_at_beginning(self, db_session, block_service, project_with_blocks):
        """시작 위치에 블록 추가 (order < 첫 블록)"""
        project, blocks = project_with_blocks

        # 첫 번째 블록(order=1.0) 앞에 추가: order=0.5
        new_block = block_service.create_block(
            db_session,
            project.id,
            text="새 블록",
            keywords=["새키워드"],
            order=0.5
        )

        assert new_block.order == 0.5
        assert new_block.text == "새 블록"

        # 전체 블록 확인
        all_blocks = block_service.get_project_blocks(db_session, project.id)
        assert len(all_blocks) == 4
        orders = [b.order for b in all_blocks]
        assert orders == [0.5, 1.0, 2.0, 3.0]

    def test_create_block_in_middle(self, db_session, block_service, project_with_blocks):
        """중간 위치에 블록 추가 (Fractional Indexing)"""
        project, blocks = project_with_blocks

        # 1.0과 2.0 사이에 추가: order=1.5
        new_block = block_service.create_block(
            db_session,
            project.id,
            text="중간 블록",
            order=1.5
        )

        assert new_block.order == 1.5

        all_blocks = block_service.get_project_blocks(db_session, project.id)
        assert len(all_blocks) == 4
        orders = [b.order for b in all_blocks]
        assert orders == [1.0, 1.5, 2.0, 3.0]

    def test_create_block_at_end(self, db_session, block_service, project_with_blocks):
        """끝에 블록 추가"""
        project, blocks = project_with_blocks

        # order 지정 안하면 마지막 블록 + 1.0
        new_block = block_service.create_block(
            db_session,
            project.id,
            text="마지막 블록"
        )

        assert new_block.order == 4.0

        all_blocks = block_service.get_project_blocks(db_session, project.id)
        assert len(all_blocks) == 4
        orders = [b.order for b in all_blocks]
        assert orders == [1.0, 2.0, 3.0, 4.0]


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
        """중간 블록 삭제 (다른 블록 order 변경 없음)"""
        project, blocks = project_with_blocks
        middle_block_id = blocks[1].id

        block_service.delete_block(db_session, middle_block_id)

        remaining = block_service.get_project_blocks(db_session, project.id)
        assert len(remaining) == 2
        # Fractional Indexing: 다른 블록의 order는 변경되지 않음
        orders = [b.order for b in remaining]
        assert orders == [1.0, 3.0]

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

    def test_split_uses_fractional_indexing(self, db_session, block_service, project_with_blocks):
        """분할 시 Fractional Indexing 사용"""
        project, blocks = project_with_blocks
        block = blocks[0]  # order=1.0
        split_pos = 10

        first, second = block_service.split_block(db_session, block.id, split_pos)

        # 첫 번째 블록은 원래 order 유지
        assert first.order == 1.0
        # 두 번째 블록은 첫 번째와 다음 블록 사이 (1.0과 2.0 사이 = 1.5)
        assert second.order == 1.5

        all_blocks = block_service.get_project_blocks(db_session, project.id)
        orders = [b.order for b in all_blocks]
        assert orders == [1.0, 1.5, 2.0, 3.0]
