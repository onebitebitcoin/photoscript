from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Block, Asset, BlockAsset
from app.models.block import BlockStatus
from app.models.block_asset import ChosenBy
from app.schemas import BlockResponse, SetPrimaryRequest, BlockAssetResponse, BlockUpdate, BlockSplitRequest, MatchOptions, BlockSearchRequest, KeywordExtractRequest, GenerateTextRequest
from app.services import extract_keywords, KeywordExtractionError, generate_block_text, TextGenerationError
from app.services.matcher import match_assets_for_block
from app.services.pexels_client import PexelsClient
from app.config import get_settings
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


@router.post("/{block_id}/match", response_model=BlockResponse)
async def match_single_block(
    block_id: str,
    options: MatchOptions = None,
    db: Session = Depends(get_db)
):
    """단일 블록 에셋 매칭"""
    logger.info(f"단일 블록 매칭 시작: block_id={block_id}")

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail={"message": "블록을 찾을 수 없습니다"})

    # 키워드가 없으면 에러
    if not block.keywords:
        raise HTTPException(
            status_code=400,
            detail={"message": "키워드가 없습니다. 먼저 키워드를 추가해주세요."}
        )

    # 옵션 설정
    if options is None:
        options = MatchOptions()

    settings = get_settings()
    max_candidates = options.max_candidates_per_block or settings.max_candidates_per_block
    video_priority = options.video_priority if options.video_priority is not None else True

    # 기존 블록-에셋 연결 삭제
    db.query(BlockAsset).filter(BlockAsset.block_id == block_id).delete()
    db.commit()

    # Pexels 클라이언트 초기화 및 에셋 매칭
    pexels_client = PexelsClient()

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
        block.status = BlockStatus.NO_RESULT
        db.commit()
        raise HTTPException(
            status_code=500,
            detail={"message": f"에셋 매칭 중 오류가 발생했습니다: {str(e)}"}
        )

    # 에셋 저장
    if assets_data:
        for i, asset_data in enumerate(assets_data):
            # 에셋 저장 (또는 기존 에셋 조회)
            existing_asset = db.query(Asset).filter(
                Asset.source_url == asset_data["source_url"]
            ).first()

            if existing_asset:
                asset = existing_asset
            else:
                asset = Asset(
                    provider=asset_data["provider"],
                    asset_type=asset_data["asset_type"],
                    source_url=asset_data["source_url"],
                    thumbnail_url=asset_data["thumbnail_url"],
                    title=asset_data.get("title"),
                    license=asset_data.get("license"),
                    meta=asset_data.get("meta")
                )
                db.add(asset)
                db.commit()
                db.refresh(asset)

            # 블록-에셋 연결
            block_asset = BlockAsset(
                block_id=block.id,
                asset_id=asset.id,
                score=asset_data.get("score", 0.0),
                is_primary=(i == 0),
                chosen_by=ChosenBy.AUTO
            )
            db.add(block_asset)

        block.status = BlockStatus.MATCHED
    else:
        block.status = BlockStatus.NO_RESULT

    db.commit()
    db.refresh(block)

    logger.info(f"단일 블록 매칭 완료: block_id={block_id}, assets_count={len(assets_data)}")

    return block


@router.post("/{block_id}/search", response_model=List[BlockAssetResponse])
async def search_assets_by_keyword(
    block_id: str,
    request: BlockSearchRequest,
    db: Session = Depends(get_db)
):
    """사용자 지정 키워드로 추가 에셋 검색"""
    logger.info(f"키워드 검색: block_id={block_id}, keyword={request.keyword}")

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail={"message": "블록을 찾을 수 없습니다"})

    # Pexels 클라이언트 초기화
    pexels_client = PexelsClient()
    settings = get_settings()

    try:
        assets_data = await match_assets_for_block(
            block.text,
            [request.keyword],  # 단일 키워드로 검색
            pexels_client,
            max_candidates=settings.max_candidates_per_block,
            video_priority=request.video_priority
        )
    except Exception as e:
        logger.error(f"키워드 검색 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": f"검색 중 오류가 발생했습니다: {str(e)}"}
        )

    # 에셋 저장 및 블록에 연결
    new_block_assets = []
    for asset_data in assets_data:
        # 기존에 같은 URL의 에셋이 있는지 확인
        existing_asset = db.query(Asset).filter(
            Asset.source_url == asset_data["source_url"]
        ).first()

        if existing_asset:
            asset = existing_asset
        else:
            asset = Asset(
                provider=asset_data["provider"],
                asset_type=asset_data["asset_type"],
                source_url=asset_data["source_url"],
                thumbnail_url=asset_data["thumbnail_url"],
                title=asset_data.get("title"),
                license=asset_data.get("license"),
                meta=asset_data.get("meta")
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)

        # 이미 블록에 연결된 에셋인지 확인
        existing_link = db.query(BlockAsset).filter(
            BlockAsset.block_id == block_id,
            BlockAsset.asset_id == asset.id
        ).first()

        if not existing_link:
            block_asset = BlockAsset(
                block_id=block.id,
                asset_id=asset.id,
                score=asset_data.get("score", 0.0),
                is_primary=False,
                chosen_by=ChosenBy.AUTO
            )
            db.add(block_asset)
            db.commit()
            db.refresh(block_asset)

            new_block_assets.append(BlockAssetResponse(
                id=block_asset.id,
                block_id=block_asset.block_id,
                asset_id=block_asset.asset_id,
                score=block_asset.score,
                is_primary=block_asset.is_primary,
                chosen_by=block_asset.chosen_by,
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
                created_at=block_asset.created_at,
                updated_at=block_asset.updated_at
            ))

    # 블록 상태 업데이트
    if new_block_assets:
        block.status = BlockStatus.MATCHED
        db.commit()

    logger.info(f"키워드 검색 완료: {len(new_block_assets)}개 새 에셋 추가")

    return new_block_assets


@router.post("/{block_id}/extract-keywords", response_model=BlockResponse)
async def extract_block_keywords(
    block_id: str,
    request: KeywordExtractRequest = None,
    db: Session = Depends(get_db)
):
    """블록 텍스트에서 키워드 자동 추출 (LLM)"""
    logger.info(f"키워드 추출 요청: block_id={block_id}")

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail={"message": "블록을 찾을 수 없습니다"})

    if not block.text or not block.text.strip():
        raise HTTPException(
            status_code=400,
            detail={"message": "블록 텍스트가 비어있습니다. 먼저 텍스트를 입력해주세요."}
        )

    # 옵션 설정
    if request is None:
        request = KeywordExtractRequest()

    try:
        keywords = await extract_keywords(block.text, max_keywords=request.max_keywords)
    except KeywordExtractionError as e:
        logger.error(f"키워드 추출 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": f"키워드 추출 실패: {str(e)}"}
        )

    # 블록 키워드 업데이트
    block.keywords = keywords
    block.status = BlockStatus.DRAFT

    # 기존 에셋 연결 삭제 (재매칭 필요)
    db.query(BlockAsset).filter(BlockAsset.block_id == block_id).delete()

    db.commit()
    db.refresh(block)

    logger.info(f"키워드 추출 완료: block_id={block_id}, keywords={keywords}")

    return block


@router.delete("/{block_id}")
async def delete_block(
    block_id: str,
    db: Session = Depends(get_db)
):
    """블록 삭제"""
    logger.info(f"블록 삭제 요청: block_id={block_id}")

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail={"message": "블록을 찾을 수 없습니다"})

    project_id = block.project_id
    deleted_index = block.index

    # 블록-에셋 연결 삭제
    db.query(BlockAsset).filter(BlockAsset.block_id == block_id).delete()

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

    logger.info(f"블록 삭제 완료: block_id={block_id}")

    return {"message": "블록이 삭제되었습니다"}


@router.post("/{block_id}/generate-text", response_model=BlockResponse)
async def generate_text_for_block(
    block_id: str,
    request: GenerateTextRequest,
    db: Session = Depends(get_db)
):
    """AI로 블록 텍스트 자동 생성 (3가지 모드)"""
    logger.info(f"텍스트 생성 요청: block_id={block_id}, mode={request.mode}, prompt={request.prompt[:50]}...")

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail={"message": "블록을 찾을 수 없습니다"})

    try:
        generated_text = await generate_block_text(
            mode=request.mode,
            prompt=request.prompt,
            user_guide=request.user_guide,
            block_id=block_id,
            db=db,
            existing_text=block.text
        )
    except TextGenerationError as e:
        logger.error(f"텍스트 생성 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": f"텍스트 생성 실패: {str(e)}"}
        )

    # 블록 텍스트 업데이트
    block.text = generated_text
    block.status = BlockStatus.DRAFT

    # 기존 에셋 연결 삭제 (재매칭 필요)
    db.query(BlockAsset).filter(BlockAsset.block_id == block_id).delete()

    db.commit()
    db.refresh(block)

    logger.info(f"텍스트 생성 완료: block_id={block_id}, text_length={len(generated_text)}")

    return block
