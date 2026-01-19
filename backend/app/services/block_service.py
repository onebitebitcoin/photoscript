"""
BlockService - 블록 관련 비즈니스 로직

Fractional Indexing 방식:
- order 필드를 Float로 사용하여 중간 삽입 시 다른 블록 수정 불필요
- 예: 1.0과 2.0 사이에 삽입 → 1.5
- 삭제 시에도 다른 블록 수정 불필요
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import Block
from app.models.block import BlockStatus
from app.services.asset_service import AssetService
from app.errors import BlockNotFoundError, BlockSplitError
from app.utils.logger import logger


class BlockService:
    """블록 관련 비즈니스 로직"""

    # order 값 간격 (새 블록 생성 시 기본 간격)
    ORDER_GAP = 1.0

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
        """프로젝트의 모든 블록 조회 (order순)"""
        return db.query(Block).filter(
            Block.project_id == project_id
        ).order_by(Block.order).all()

    # ==========================================================================
    # 생성/수정/삭제
    # ==========================================================================

    def create_block(
        self,
        db: Session,
        project_id: str,
        text: str,
        keywords: List[str] = None,
        order: float = None
    ) -> Block:
        """
        새 블록 생성 (Fractional Indexing)

        Args:
            db: DB 세션
            project_id: 프로젝트 ID
            text: 블록 텍스트
            keywords: 키워드 리스트
            order: 블록 순서 (None이면 맨 뒤에 추가)

        다른 블록의 order 값을 변경하지 않음 - 단순 INSERT만 수행
        """
        try:
            # order가 지정되지 않으면 맨 뒤에 추가
            if order is None:
                last_block = db.query(Block).filter(
                    Block.project_id == project_id
                ).order_by(Block.order.desc()).first()

                if last_block:
                    order = last_block.order + self.ORDER_GAP
                else:
                    order = self.ORDER_GAP

            # 새 블록 생성 - INSERT만 수행, 다른 블록 수정 없음
            new_block = Block(
                project_id=project_id,
                order=order,
                text=text,
                keywords=keywords or [],
                status=BlockStatus.DRAFT
            )
            db.add(new_block)
            db.commit()
            db.refresh(new_block)

            logger.info(f"블록 생성: block_id={new_block.id}, order={new_block.order}")
            return new_block
        except Exception as e:
            db.rollback()
            logger.error(f"블록 생성 실패: {str(e)}", exc_info=True)
            raise

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
        블록 삭제 (Fractional Indexing)

        다른 블록의 order 값을 변경하지 않음 - 단순 DELETE만 수행
        """
        try:
            block = self.get_block(db, block_id)

            # 에셋 연결 삭제
            self.asset_service.delete_block_assets(db, block_id, auto_commit=False)

            # 블록 삭제 - DELETE만 수행, 다른 블록 수정 없음
            db.delete(block)
            db.commit()

            logger.info(f"블록 삭제: block_id={block_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"블록 삭제 실패: {str(e)}", exc_info=True)
            raise

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
        블록을 두 개로 나누기 (Fractional Indexing)

        Args:
            db: DB 세션
            block_id: 블록 ID
            split_position: 분할 위치 (문자 인덱스)

        Returns:
            Tuple[Block, Block]: (첫 번째 블록, 두 번째 블록)

        두 번째 블록의 order는 원본과 다음 블록 사이의 중간값
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

        # 다음 블록 찾기 (order가 현재 블록보다 큰 첫 번째 블록)
        next_block = db.query(Block).filter(
            Block.project_id == block.project_id,
            Block.order > block.order
        ).order_by(Block.order).first()

        # 새 블록의 order 계산 (원본과 다음 블록 사이의 중간값)
        if next_block:
            new_order = (block.order + next_block.order) / 2
        else:
            new_order = block.order + self.ORDER_GAP

        # 두 번째 블록 생성
        new_block = Block(
            project_id=block.project_id,
            order=new_order,
            text=second_text,
            keywords=block.keywords[3:] if block.keywords and len(block.keywords) > 3 else [],
            status=BlockStatus.DRAFT
        )
        db.add(new_block)

        db.commit()
        db.refresh(block)
        db.refresh(new_block)

        logger.info(f"블록 분할: {block_id} -> {block.id}, {new_block.id}")
        return block, new_block

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
    # order 재정렬 (주기적 정리용)
    # ==========================================================================

    def reindex_blocks(self, db: Session, project_id: str) -> List[Block]:
        """
        프로젝트 내 모든 블록 order 재정렬

        Fractional indexing으로 인해 order 값이 너무 정밀해지면
        주기적으로 정수 간격으로 재정렬 (1.0, 2.0, 3.0, ...)
        """
        blocks = db.query(Block).filter(
            Block.project_id == project_id
        ).order_by(Block.order).all()

        for idx, block in enumerate(blocks):
            block.order = float(idx + 1) * self.ORDER_GAP

        db.commit()
        logger.info(f"블록 order 재정렬: project_id={project_id}, count={len(blocks)}")
        return blocks
