from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Block, Asset, BlockAsset
from app.models.block import BlockStatus
from app.models.block_asset import ChosenBy
from app.schemas import BlockResponse, SetPrimaryRequest, BlockAssetResponse
from app.utils.logger import logger

router = APIRouter()


@router.get("/{block_id}/assets", response_model=List[BlockAssetResponse])
async def get_block_assets(
    block_id: str,
    db: Session = Depends(get_db)
):
    """블록의 에셋 후보 목록 조회"""
    logger.info(f"블록 에셋 조회: block_id={block_id}")

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail={"message": "블록을 찾을 수 없습니다"})

    # 블록-에셋 연결 조회 (점수순 정렬)
    block_assets = db.query(BlockAsset).filter(
        BlockAsset.block_id == block_id
    ).order_by(BlockAsset.score.desc()).all()

    result = []
    for ba in block_assets:
        asset = db.query(Asset).filter(Asset.id == ba.asset_id).first()
        if asset:
            result.append(BlockAssetResponse(
                id=ba.id,
                block_id=ba.block_id,
                asset_id=ba.asset_id,
                score=ba.score,
                is_primary=ba.is_primary,
                chosen_by=ba.chosen_by,
                asset={
                    "id": asset.id,
                    "provider": asset.provider,
                    "asset_type": asset.asset_type,
                    "source_url": asset.source_url,
                    "thumbnail_url": asset.thumbnail_url,
                    "title": asset.title,
                    "license": asset.license,
                    "meta": asset.meta,
                    "created_at": asset.created_at
                },
                created_at=ba.created_at,
                updated_at=ba.updated_at
            ))

    return result


@router.post("/{block_id}/primary", response_model=BlockResponse)
async def set_primary_asset(
    block_id: str,
    request: SetPrimaryRequest,
    db: Session = Depends(get_db)
):
    """대표 에셋 선택 (Use this)"""
    logger.info(f"대표 에셋 선택: block_id={block_id}, asset_id={request.asset_id}")

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail={"message": "블록을 찾을 수 없습니다"})

    # 해당 블록-에셋 연결 확인
    target_ba = db.query(BlockAsset).filter(
        BlockAsset.block_id == block_id,
        BlockAsset.asset_id == request.asset_id
    ).first()

    if not target_ba:
        raise HTTPException(
            status_code=404,
            detail={"message": "해당 에셋이 이 블록의 후보에 없습니다"}
        )

    # 기존 대표 해제
    db.query(BlockAsset).filter(
        BlockAsset.block_id == block_id,
        BlockAsset.is_primary == True
    ).update({"is_primary": False, "chosen_by": ChosenBy.AUTO})

    # 새 대표 설정
    target_ba.is_primary = True
    target_ba.chosen_by = ChosenBy.USER

    # 블록 상태 업데이트
    block.status = BlockStatus.CUSTOM

    db.commit()
    db.refresh(block)

    logger.info(f"대표 에셋 선택 완료: block_id={block_id}")

    return block
