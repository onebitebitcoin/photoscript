"""
AssetService - 에셋 저장/조회 서비스

Unix 철학 원칙 적용:
- 원칙 1 (모듈성): 에셋 관련 로직을 단일 모듈로 분리
- 원칙 5 (단순성): 중복 코드 통합
- 원칙 8 (견고성): 명시적 에러 타입
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import Asset, BlockAsset
from app.models.block_asset import ChosenBy
from app.errors import AssetSaveError, AssetNotFoundError
from app.utils.logger import logger


class AssetService:
    """에셋 저장/조회 서비스"""

    def get_or_create_asset(
        self,
        db: Session,
        asset_data: Dict[str, Any]
    ) -> Asset:
        """
        source_url 기준으로 기존 에셋 조회 또는 새 에셋 생성

        Args:
            db: DB 세션
            asset_data: 에셋 데이터 딕셔너리
                - provider: 제공자 (예: "pexels")
                - asset_type: 에셋 타입 ("IMAGE" or "VIDEO")
                - source_url: 원본 URL
                - thumbnail_url: 썸네일 URL
                - title: 제목 (optional)
                - license: 라이선스 (optional)
                - meta: 메타데이터 (optional)

        Returns:
            Asset: 조회되거나 생성된 에셋
        """
        source_url = asset_data.get("source_url")
        if not source_url:
            raise AssetSaveError("source_url이 필요합니다")

        # 기존 에셋 조회
        existing_asset = db.query(Asset).filter(
            Asset.source_url == source_url
        ).first()

        if existing_asset:
            logger.debug(f"기존 에셋 사용: id={existing_asset.id}")
            return existing_asset

        # 새 에셋 생성
        asset = Asset(
            provider=asset_data.get("provider"),
            asset_type=asset_data.get("asset_type"),
            source_url=source_url,
            thumbnail_url=asset_data.get("thumbnail_url"),
            title=asset_data.get("title"),
            license=asset_data.get("license"),
            meta=asset_data.get("meta")
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

        logger.debug(f"새 에셋 생성: id={asset.id}")
        return asset

    def save_and_link_assets(
        self,
        db: Session,
        block_id: str,
        assets_data: List[Dict[str, Any]],
        clear_existing: bool = True
    ) -> List[BlockAsset]:
        """
        에셋 저장 + 블록 연결

        Args:
            db: DB 세션
            block_id: 블록 ID
            assets_data: 에셋 데이터 리스트
            clear_existing: True면 기존 연결 삭제 후 새로 연결

        Returns:
            List[BlockAsset]: 생성된 블록-에셋 연결 리스트
        """
        if clear_existing:
            db.query(BlockAsset).filter(BlockAsset.block_id == block_id).delete()
            db.commit()

        block_assets = []
        for i, asset_data in enumerate(assets_data):
            # 에셋 저장 (또는 기존 에셋 조회)
            asset = self.get_or_create_asset(db, asset_data)

            # 블록-에셋 연결
            block_asset = BlockAsset(
                block_id=block_id,
                asset_id=asset.id,
                score=asset_data.get("score", 0.0),
                is_primary=(i == 0),  # 첫 번째가 대표
                chosen_by=ChosenBy.AUTO
            )
            db.add(block_asset)
            block_assets.append(block_asset)

        db.commit()

        logger.info(f"블록 {block_id}에 {len(block_assets)}개 에셋 연결 완료")
        return block_assets

    def add_asset_to_block(
        self,
        db: Session,
        block_id: str,
        asset_data: Dict[str, Any],
        is_primary: bool = False
    ) -> Optional[BlockAsset]:
        """
        단일 에셋을 블록에 추가 (기존 연결 유지)

        중복 에셋은 스킵

        Args:
            db: DB 세션
            block_id: 블록 ID
            asset_data: 에셋 데이터
            is_primary: 대표 에셋 여부

        Returns:
            BlockAsset or None: 생성된 연결 (중복 시 None)
        """
        # 에셋 저장 (또는 기존 에셋 조회)
        asset = self.get_or_create_asset(db, asset_data)

        # 이미 블록에 연결된 에셋인지 확인
        existing_link = db.query(BlockAsset).filter(
            BlockAsset.block_id == block_id,
            BlockAsset.asset_id == asset.id
        ).first()

        if existing_link:
            logger.debug(f"이미 연결된 에셋: block_id={block_id}, asset_id={asset.id}")
            return None

        # 블록-에셋 연결
        block_asset = BlockAsset(
            block_id=block_id,
            asset_id=asset.id,
            score=asset_data.get("score", 0.0),
            is_primary=is_primary,
            chosen_by=ChosenBy.AUTO
        )
        db.add(block_asset)
        db.commit()
        db.refresh(block_asset)

        logger.debug(f"에셋 추가: block_id={block_id}, asset_id={asset.id}")
        return block_asset

    def get_block_assets(
        self,
        db: Session,
        block_id: str
    ) -> List[Dict[str, Any]]:
        """
        블록의 에셋 목록 조회 (점수순 정렬)

        Args:
            db: DB 세션
            block_id: 블록 ID

        Returns:
            List[Dict]: 에셋 정보 리스트
        """
        block_assets = db.query(BlockAsset).filter(
            BlockAsset.block_id == block_id
        ).order_by(BlockAsset.score.desc()).all()

        result = []
        for ba in block_assets:
            asset = db.query(Asset).filter(Asset.id == ba.asset_id).first()
            if asset:
                result.append({
                    "block_asset": ba,
                    "asset": asset
                })

        return result

    def set_primary_asset(
        self,
        db: Session,
        block_id: str,
        asset_id: str
    ) -> BlockAsset:
        """
        대표 에셋 설정

        Args:
            db: DB 세션
            block_id: 블록 ID
            asset_id: 에셋 ID

        Returns:
            BlockAsset: 대표로 설정된 블록-에셋 연결

        Raises:
            AssetNotFoundError: 해당 블록에 에셋이 없을 때
        """
        # 해당 블록-에셋 연결 확인
        target_ba = db.query(BlockAsset).filter(
            BlockAsset.block_id == block_id,
            BlockAsset.asset_id == asset_id
        ).first()

        if not target_ba:
            raise AssetNotFoundError(
                "해당 에셋이 이 블록의 후보에 없습니다",
                {"block_id": block_id, "asset_id": asset_id}
            )

        # 기존 대표 해제
        db.query(BlockAsset).filter(
            BlockAsset.block_id == block_id,
            BlockAsset.is_primary == True
        ).update({"is_primary": False, "chosen_by": ChosenBy.AUTO})

        # 새 대표 설정
        target_ba.is_primary = True
        target_ba.chosen_by = ChosenBy.USER

        db.commit()
        db.refresh(target_ba)

        logger.info(f"대표 에셋 설정: block_id={block_id}, asset_id={asset_id}")
        return target_ba

    def delete_block_assets(
        self,
        db: Session,
        block_id: str
    ) -> int:
        """
        블록의 모든 에셋 연결 삭제

        Args:
            db: DB 세션
            block_id: 블록 ID

        Returns:
            int: 삭제된 연결 수
        """
        deleted_count = db.query(BlockAsset).filter(
            BlockAsset.block_id == block_id
        ).delete()
        db.commit()

        logger.debug(f"블록 에셋 연결 삭제: block_id={block_id}, count={deleted_count}")
        return deleted_count
