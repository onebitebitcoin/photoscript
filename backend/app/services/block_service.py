"""
BlockService - 블록 관련 비즈니스 로직

Unix 철학 원칙 적용:
- 원칙 1 (모듈성): 블록 관련 로직을 단일 모듈로 분리
- 원칙 4 (분리): Router(인터페이스) / Service(비즈니스 로직) / Model(데이터)
- 원칙 5 (단순성): 중복 코드 통합
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import Block, Project
from app.models.block import BlockStatus
from app.services.asset_service import AssetService
from app.errors import BlockNotFoundError, BlockValidationError, BlockMergeError, BlockSplitError
from app.utils.logger import logger


class BlockService:
    """블록 관련 비즈니스 로직"""

    def __init__(self):
        self.asset_service = AssetService()

    # ==========================================================================
    # 조회
    # ==========================================================================

    def get_block(self, db: Session, block_id: str) -> Block:
        """
        블록 조회

        Raises:
            BlockNotFoundError: 블록을 찾을 수 없을 때
        """
        block = db.query(Block).filter(Block.id == block_id).first()
        if not block:
            raise BlockNotFoundError("블록을 찾을 수 없습니다", {"block_id": block_id})
        return block

    def get_project_blocks(
        self,
        db: Session,
        project_id: str
    ) -> List[Block]:
        """프로젝트의 모든 블록 조회 (인덱스순)"""
        return db.query(Block).filter(
            Block.project_id == project_id
        ).order_by(Block.index).all()

    # ==========================================================================
    # 생성/수정/삭제
    # ==========================================================================

    def create_block(
        self,
        db: Session,
        project_id: str,
        text: str,
        keywords: List[str] = None,
        insert_at: int = 0
    ) -> Block:
        """
        새 블록 생성

        Args:
            db: DB 세션
            project_id: 프로젝트 ID
            text: 블록 텍스트
            keywords: 키워드 리스트
            insert_at: 삽입 위치 인덱스
        """
        # 기존 블록들의 인덱스 조정 (insert_at 이상인 블록들 +1)
        existing_blocks = db.query(Block).filter(
            Block.project_id == project_id,
            Block.index >= insert_at
        ).order_by(Block.index.desc()).all()

        for block in existing_blocks:
            block.index += 1

        db.commit()

        # 새 블록 생성
        new_block = Block(
            project_id=project_id,
            index=insert_at,
            text=text,
            keywords=keywords or [],
            status=BlockStatus.DRAFT
        )
        db.add(new_block)
        db.commit()
        db.refresh(new_block)

        logger.info(f"블록 생성: block_id={new_block.id}, index={new_block.index}")
        return new_block

    def update_block(
        self,
        db: Session,
        block_id: str,
        text: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> Block:
        """
        블록 수정

        수정 시 에셋 연결이 삭제되고 상태가 DRAFT로 변경됨
        """
        block = self.get_block(db, block_id)

        if text is not None:
            block.text = text

        if keywords is not None:
            block.keywords = keywords

        # 상태를 DRAFT로 변경
        block.status = BlockStatus.DRAFT

        # 에셋 연결 삭제
        self.asset_service.delete_block_assets(db, block_id)

        db.commit()
        db.refresh(block)

        logger.info(f"블록 수정: block_id={block_id}")
        return block

    def delete_block(self, db: Session, block_id: str) -> None:
        """
        블록 삭제

        삭제 후 후속 블록들의 인덱스 재정렬
        """
        block = self.get_block(db, block_id)
        project_id = block.project_id
        deleted_index = block.index

        # 에셋 연결 삭제
        self.asset_service.delete_block_assets(db, block_id)

        # 블록 삭제
        db.delete(block)
        db.commit()

        # 후속 블록들 인덱스 재정렬
        subsequent_blocks = db.query(Block).filter(
            Block.project_id == project_id,
            Block.index > deleted_index
        ).order_by(Block.index).all()

        for b in subsequent_blocks:
            b.index -= 1

        db.commit()

        logger.info(f"블록 삭제: block_id={block_id}")

    # ==========================================================================
    # 분할/합치기
    # ==========================================================================

    def split_block(
        self,
        db: Session,
        block_id: str,
        split_position: int
    ) -> Tuple[Block, Block]:
        """
        블록을 두 개로 나누기

        Args:
            db: DB 세션
            block_id: 블록 ID
            split_position: 분할 위치 (문자 인덱스)

        Returns:
            Tuple[Block, Block]: (첫 번째 블록, 두 번째 블록)

        Raises:
            BlockSplitError: 분할 위치가 유효하지 않을 때
        """
        block = self.get_block(db, block_id)
        text = block.text
        position = split_position

        # 위치 검증
        if position <= 0 or position >= len(text):
            raise BlockSplitError(
                f"유효하지 않은 위치입니다. 1 ~ {len(text)-1} 사이여야 합니다.",
                {"position": position, "text_length": len(text)}
            )

        # 텍스트 분할
        first_text = text[:position].strip()
        second_text = text[position:].strip()

        if not first_text or not second_text:
            raise BlockSplitError(
                "분할 후 빈 블록이 생성됩니다. 다른 위치를 선택해주세요.",
                {"first_text": first_text, "second_text": second_text}
            )

        # 에셋 연결 삭제
        self.asset_service.delete_block_assets(db, block_id)

        # 첫 번째 블록 업데이트
        block.text = first_text
        block.keywords = block.keywords[:3] if block.keywords else []
        block.status = BlockStatus.DRAFT

        # 두 번째 블록 생성
        new_block = Block(
            project_id=block.project_id,
            index=block.index + 1,
            text=second_text,
            keywords=block.keywords[3:] if block.keywords and len(block.keywords) > 3 else [],
            status=BlockStatus.DRAFT
        )
        db.add(new_block)
        db.commit()

        # 후속 블록들 인덱스 업데이트
        subsequent_blocks = db.query(Block).filter(
            Block.project_id == block.project_id,
            Block.index > block.index,
            Block.id != new_block.id
        ).order_by(Block.index).all()

        for b in subsequent_blocks:
            b.index += 1

        db.commit()
        db.refresh(block)
        db.refresh(new_block)

        logger.info(f"블록 분할: {block_id} -> {block.id}, {new_block.id}")
        return block, new_block

    def merge_blocks(
        self,
        db: Session,
        project_id: str,
        block_ids: List[str]
    ) -> Block:
        """
        여러 블록을 하나로 합치기

        Args:
            db: DB 세션
            project_id: 프로젝트 ID
            block_ids: 합칠 블록 ID 리스트

        Returns:
            Block: 합쳐진 블록

        Raises:
            BlockMergeError: 합칠 수 없을 때
        """
        # 블록 조회
        blocks = db.query(Block).filter(
            Block.id.in_(block_ids),
            Block.project_id == project_id
        ).order_by(Block.index).all()

        if len(blocks) != len(block_ids):
            raise BlockMergeError(
                "일부 블록을 찾을 수 없습니다",
                {"requested": block_ids, "found": [b.id for b in blocks]}
            )

        # 인접한 블록인지 확인
        indices = [b.index for b in blocks]
        for i in range(len(indices) - 1):
            if indices[i + 1] - indices[i] != 1:
                raise BlockMergeError(
                    "인접한 블록만 합칠 수 있습니다",
                    {"indices": indices}
                )

        # 첫 번째 블록에 텍스트 합치기
        merged_text = "\n\n".join([b.text for b in blocks])
        merged_keywords = []
        for b in blocks:
            if b.keywords:
                for kw in b.keywords:
                    if kw not in merged_keywords:
                        merged_keywords.append(kw)

        first_block = blocks[0]
        first_block.text = merged_text
        first_block.keywords = merged_keywords[:10]  # 최대 10개
        first_block.status = BlockStatus.DRAFT

        # 나머지 블록 삭제
        for block in blocks[1:]:
            self.asset_service.delete_block_assets(db, block.id)
            db.delete(block)

        # 인덱스 재정렬
        remaining_blocks = db.query(Block).filter(
            Block.project_id == project_id
        ).order_by(Block.index).all()

        for new_idx, block in enumerate(remaining_blocks):
            block.index = new_idx

        db.commit()
        db.refresh(first_block)

        logger.info(f"블록 합치기: {len(block_ids)}개 -> 1개")
        return first_block

    # ==========================================================================
    # 상태 변경
    # ==========================================================================

    def update_block_status(
        self,
        db: Session,
        block_id: str,
        status: BlockStatus
    ) -> Block:
        """블록 상태 변경"""
        block = self.get_block(db, block_id)
        block.status = status
        db.commit()
        db.refresh(block)
        return block

    def update_block_keywords(
        self,
        db: Session,
        block_id: str,
        keywords: List[str]
    ) -> Block:
        """
        블록 키워드 업데이트

        키워드 업데이트 시 에셋 연결 삭제 및 상태 DRAFT로 변경
        """
        block = self.get_block(db, block_id)
        block.keywords = keywords
        block.status = BlockStatus.DRAFT

        # 에셋 연결 삭제
        self.asset_service.delete_block_assets(db, block_id)

        db.commit()
        db.refresh(block)

        logger.info(f"키워드 업데이트: block_id={block_id}, keywords={keywords}")
        return block

    def update_block_text(
        self,
        db: Session,
        block_id: str,
        text: str
    ) -> Block:
        """
        블록 텍스트 업데이트

        텍스트 업데이트 시 에셋 연결 삭제 및 상태 DRAFT로 변경
        """
        block = self.get_block(db, block_id)
        block.text = text
        block.status = BlockStatus.DRAFT

        # 에셋 연결 삭제
        self.asset_service.delete_block_assets(db, block_id)

        db.commit()
        db.refresh(block)

        logger.info(f"텍스트 업데이트: block_id={block_id}")
        return block

    # ==========================================================================
    # 인덱스 재정렬
    # ==========================================================================

    def reindex_blocks(self, db: Session, project_id: str) -> List[Block]:
        """프로젝트 내 모든 블록 인덱스 재정렬"""
        blocks = db.query(Block).filter(
            Block.project_id == project_id
        ).order_by(Block.index).all()

        for new_idx, block in enumerate(blocks):
            block.index = new_idx

        db.commit()
        return blocks
