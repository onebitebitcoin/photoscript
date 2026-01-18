"""
ProjectService - 프로젝트 워크플로우 서비스

Unix 철학 원칙 적용:
- 원칙 1 (모듈성): 프로젝트 워크플로우 로직을 단일 모듈로 분리
- 원칙 4 (분리): Router(인터페이스) / Service(비즈니스 로직) / Model(데이터)
- 원칙 5 (단순성): 워크플로우 조합 로직 통합
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Project, Block
from app.models.block import BlockStatus
from app.services.asset_service import AssetService
from app.services.pexels_client import PexelsClient
from app.services.matcher import match_assets_for_block
from app.services import process_script
from app.errors import ProjectNotFoundError
from app.utils.logger import logger


class ProjectService:
    """프로젝트 워크플로우 서비스"""

    def __init__(self):
        self.asset_service = AssetService()

    # ==========================================================================
    # 조회
    # ==========================================================================

    def get_project(self, db: Session, project_id: str) -> Project:
        """
        프로젝트 조회

        Raises:
            ProjectNotFoundError: 프로젝트를 찾을 수 없을 때
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ProjectNotFoundError("프로젝트를 찾을 수 없습니다", {"project_id": project_id})
        return project

    def get_projects(self, db: Session) -> List[Project]:
        """프로젝트 목록 조회 (최신순)"""
        return db.query(Project).order_by(Project.created_at.desc()).all()

    # ==========================================================================
    # 생성/삭제
    # ==========================================================================

    def create_project(
        self,
        db: Session,
        title: Optional[str],
        script_raw: str
    ) -> Project:
        """프로젝트 생성"""
        project = Project(
            title=title,
            script_raw=script_raw
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        logger.info(f"프로젝트 생성: id={project.id}")
        return project

    def delete_project(self, db: Session, project_id: str) -> None:
        """
        프로젝트 삭제

        관련된 블록, 에셋 연결도 모두 삭제
        """
        project = self.get_project(db, project_id)

        # 연관된 블록-에셋 연결 삭제
        blocks = db.query(Block).filter(Block.project_id == project_id).all()
        for block in blocks:
            self.asset_service.delete_block_assets(db, block.id)

        # 블록 삭제
        db.query(Block).filter(Block.project_id == project_id).delete()

        # 프로젝트 삭제
        db.delete(project)
        db.commit()

        logger.info(f"프로젝트 삭제: id={project_id}")

    # ==========================================================================
    # 워크플로우: Generate (분할 + 매칭)
    # ==========================================================================

    async def generate_visuals(
        self,
        db: Session,
        project_id: str,
        max_candidates: int = 5
    ) -> int:
        """
        스크립트 분할 + 에셋 매칭 워크플로우

        Args:
            db: DB 세션
            project_id: 프로젝트 ID
            max_candidates: 블록당 최대 에셋 후보 수

        Returns:
            int: 생성된 블록 수
        """
        project = self.get_project(db, project_id)

        # 기존 블록 삭제
        db.query(Block).filter(Block.project_id == project_id).delete()
        db.commit()

        # Step 1: LLM으로 스크립트 분할 + 키워드 추출
        logger.info("Step 1: LLM으로 스크립트 처리")
        processed_blocks = await process_script(project.script_raw)

        if not processed_blocks:
            return 0

        # Pexels 클라이언트 초기화
        pexels_client = PexelsClient()

        # Step 2: 각 블록 생성 및 에셋 매칭
        logger.info(f"Step 2: {len(processed_blocks)}개 블록 에셋 매칭 시작")

        for idx, block_data in enumerate(processed_blocks):
            text = block_data["text"]
            keywords = block_data.get("keywords", [])

            # 블록 생성
            block = Block(
                project_id=project_id,
                index=idx,
                text=text,
                keywords=keywords,
                status=BlockStatus.PENDING
            )
            db.add(block)
            db.commit()
            db.refresh(block)

            # 키워드가 없으면 NO_RESULT
            if not keywords:
                block.status = BlockStatus.NO_RESULT
                db.commit()
                continue

            # 에셋 매칭
            try:
                assets_data = await match_assets_for_block(
                    text, keywords, pexels_client, max_candidates=max_candidates
                )
            except Exception as e:
                logger.error(f"에셋 매칭 실패: {e}")
                assets_data = []

            # 에셋 저장
            if assets_data:
                self.asset_service.save_and_link_assets(db, block.id, assets_data, clear_existing=False)
                block.status = BlockStatus.MATCHED
            else:
                block.status = BlockStatus.NO_RESULT

            db.commit()

        logger.info(f"Generate 완료: {len(processed_blocks)}개 블록 생성")
        return len(processed_blocks)

    # ==========================================================================
    # 워크플로우: Split (분할만)
    # ==========================================================================

    async def split_script(
        self,
        db: Session,
        project_id: str,
        max_keywords: int = 5
    ) -> List[Block]:
        """
        스크립트 분할 워크플로우 (에셋 매칭 없이)

        Args:
            db: DB 세션
            project_id: 프로젝트 ID
            max_keywords: 블록당 최대 키워드 수

        Returns:
            List[Block]: 생성된 블록 리스트
        """
        project = self.get_project(db, project_id)

        # 기존 블록 삭제
        db.query(Block).filter(Block.project_id == project_id).delete()
        db.commit()

        # LLM으로 스크립트 분할 + 키워드 추출
        logger.info("LLM으로 스크립트 처리")
        processed_blocks = await process_script(project.script_raw, max_keywords=max_keywords)

        if not processed_blocks:
            return []

        # 블록 생성
        blocks = []
        for idx, block_data in enumerate(processed_blocks):
            block = Block(
                project_id=project_id,
                index=idx,
                text=block_data["text"],
                keywords=block_data.get("keywords", []),
                status=BlockStatus.DRAFT
            )
            db.add(block)
            db.commit()
            db.refresh(block)
            blocks.append(block)

        logger.info(f"Split 완료: {len(blocks)}개 블록 생성")
        return blocks

    # ==========================================================================
    # 워크플로우: Match (매칭만)
    # ==========================================================================

    async def match_all_blocks(
        self,
        db: Session,
        project_id: str,
        max_candidates: int = 5,
        video_priority: bool = True
    ) -> int:
        """
        모든 블록 에셋 매칭 워크플로우

        Args:
            db: DB 세션
            project_id: 프로젝트 ID
            max_candidates: 블록당 최대 에셋 후보 수
            video_priority: 영상 우선 여부

        Returns:
            int: 매칭 성공한 블록 수
        """
        self.get_project(db, project_id)

        # 블록 조회
        blocks = db.query(Block).filter(
            Block.project_id == project_id
        ).order_by(Block.index).all()

        if not blocks:
            return 0

        # Pexels 클라이언트 초기화
        pexels_client = PexelsClient()

        matched_count = 0
        for block in blocks:
            # 키워드가 없으면 NO_RESULT
            if not block.keywords:
                self.asset_service.delete_block_assets(db, block.id)
                block.status = BlockStatus.NO_RESULT
                db.commit()
                continue

            # 에셋 매칭
            try:
                assets_data = await match_assets_for_block(
                    block.text,
                    block.keywords,
                    pexels_client,
                    max_candidates=max_candidates,
                    video_priority=video_priority
                )
            except Exception as e:
                logger.error(f"에셋 매칭 실패: {e}")
                assets_data = []

            # 에셋 저장
            if assets_data:
                self.asset_service.save_and_link_assets(db, block.id, assets_data, clear_existing=True)
                block.status = BlockStatus.MATCHED
                matched_count += 1
            else:
                self.asset_service.delete_block_assets(db, block.id)
                block.status = BlockStatus.NO_RESULT

            db.commit()

        logger.info(f"Match 완료: {matched_count}/{len(blocks)}개 블록 매칭 성공")
        return matched_count
