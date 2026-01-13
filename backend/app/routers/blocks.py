from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Block, Asset, BlockAsset
from app.models.block import BlockStatus
from app.models.block_asset import ChosenBy
from app.schemas import BlockResponse, SetPrimaryRequest, BlockAssetResponse, BlockUpdate, BlockSplitRequest
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


@router.put("/{block_id}", response_model=BlockResponse)
async def update_block(
    block_id: str,
    request: BlockUpdate,
    db: Session = Depends(get_db)
):
    """블록 텍스트/키워드 수정"""
    logger.info(f"블록 수정: block_id={block_id}")

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail={"message": "블록을 찾을 수 없습니다"})

    # 텍스트 수정
    if request.text is not None:
        block.text = request.text

    # 키워드 수정
    if request.keywords is not None:
        block.keywords = request.keywords

    # 상태를 DRAFT로 변경 (재매칭 필요)
    block.status = BlockStatus.DRAFT

    # 기존 에셋 연결 삭제 (재매칭 필요하므로)
    db.query(BlockAsset).filter(BlockAsset.block_id == block_id).delete()

    db.commit()
    db.refresh(block)

    logger.info(f"블록 수정 완료: block_id={block_id}")

    return block


@router.post("/{block_id}/split", response_model=List[BlockResponse])
async def split_block(
    block_id: str,
    request: BlockSplitRequest,
    db: Session = Depends(get_db)
):
    """블록을 두 개로 나누기"""
    logger.info(f"블록 나누기: block_id={block_id}, position={request.split_position}")

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail={"message": "블록을 찾을 수 없습니다"})

    text = block.text
    position = request.split_position

    # 위치 검증
    if position <= 0 or position >= len(text):
        raise HTTPException(
            status_code=400,
            detail={"message": f"유효하지 않은 위치입니다. 1 ~ {len(text)-1} 사이여야 합니다."}
        )

    # 텍스트 분할
    first_text = text[:position].strip()
    second_text = text[position:].strip()

    if not first_text or not second_text:
        raise HTTPException(
            status_code=400,
            detail={"message": "분할 후 빈 블록이 생성됩니다. 다른 위치를 선택해주세요."}
        )

    # 기존 블록-에셋 연결 삭제
    db.query(BlockAsset).filter(BlockAsset.block_id == block_id).delete()

    # 첫 번째 블록 업데이트
    block.text = first_text
    block.keywords = block.keywords[:3] if block.keywords else []  # 키워드 절반
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

    logger.info(f"블록 나누기 완료: {block_id} → {block.id}, {new_block.id}")

    return [block, new_block]


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
