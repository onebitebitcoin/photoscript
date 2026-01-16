from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Block, Asset, BlockAsset
from app.models.block import BlockStatus
from app.models.block_asset import ChosenBy
from app.schemas import BlockResponse, SetPrimaryRequest, BlockAssetResponse, BlockUpdate, BlockSplitRequest, MatchOptions, BlockSearchRequest, KeywordExtractRequest, GenerateTextRequest, GenerateTextResponse, GenerationInfo
from app.services import extract_keywords, KeywordExtractionError, generate_block_text_auto, TextGenerationError
from app.services.matcher import match_assets_for_block
from app.services.pexels_client import PexelsClient
from app.services.asset_service import AssetService
from app.services.block_service import BlockService
from app.errors import AssetNotFoundError, BlockNotFoundError, BlockSplitError
from app.config import get_settings
from app.utils.logger import logger

router = APIRouter()
asset_service = AssetService()
block_service = BlockService()


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

    try:
        block = block_service.update_block(
            db, block_id,
            text=request.text,
            keywords=request.keywords
        )
    except BlockNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": e.message})

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

    try:
        first_block, second_block = block_service.split_block(
            db, block_id, request.split_position
        )
    except BlockNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": e.message})
    except BlockSplitError as e:
        raise HTTPException(status_code=400, detail={"message": e.message})

    logger.info(f"블록 나누기 완료: {block_id} -> {first_block.id}, {second_block.id}")
    return [first_block, second_block]


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

    # AssetService로 대표 에셋 설정
    try:
        asset_service.set_primary_asset(db, block_id, request.asset_id)
    except AssetNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": e.message})

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
        asset_service.delete_block_assets(db, block_id)
        block.status = BlockStatus.NO_RESULT
        db.commit()
        raise HTTPException(
            status_code=500,
            detail={"message": f"에셋 매칭 중 오류가 발생했습니다: {str(e)}"}
        )

    # 에셋 저장 (AssetService 사용)
    if assets_data:
        asset_service.save_and_link_assets(db, block.id, assets_data, clear_existing=True)
        block.status = BlockStatus.MATCHED
    else:
        asset_service.delete_block_assets(db, block_id)
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

    # 에셋 저장 및 블록에 연결 (AssetService 사용)
    new_block_assets = []
    for asset_data in assets_data:
        block_asset = asset_service.add_asset_to_block(db, block.id, asset_data)

        if block_asset:
            # 에셋 조회
            asset = db.query(Asset).filter(Asset.id == block_asset.asset_id).first()

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

    # 기존 에셋 연결 삭제 (AssetService 사용)
    asset_service.delete_block_assets(db, block_id)

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

    try:
        block_service.delete_block(db, block_id)
    except BlockNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": e.message})

    logger.info(f"블록 삭제 완료: block_id={block_id}")
    return {"message": "블록이 삭제되었습니다"}


@router.post("/{block_id}/generate-text", response_model=GenerateTextResponse)
async def generate_text_for_block(
    block_id: str,
    request: GenerateTextRequest,
    db: Session = Depends(get_db)
):
    """AI로 블록 텍스트 자동 생성 (자동 모드 판단)

    - URL 포함 시: 해당 URL 콘텐츠를 읽어서 참고
    - '검색해서', '찾아서' 등 포함 시: 웹 검색 후 생성
    - 그 외: 컨텍스트만으로 텍스트 생성
    """
    logger.info(f"텍스트 생성 요청: block_id={block_id}, prompt={request.prompt[:50]}...")

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail={"message": "블록을 찾을 수 없습니다"})

    try:
        result = await generate_block_text_auto(
            prompt=request.prompt,
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
    except Exception as e:
        logger.error(f"텍스트 생성 중 예상치 못한 에러: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"message": f"텍스트 생성 중 에러 발생: {type(e).__name__}: {str(e)}"}
        )

    # 블록 텍스트 업데이트
    block.text = result.text
    block.status = BlockStatus.DRAFT

    # 기존 에셋 연결 삭제 (AssetService 사용)
    asset_service.delete_block_assets(db, block_id)

    db.commit()
    db.refresh(block)

    logger.info(f"텍스트 생성 완료: block_id={block_id}, mode={result.mode}, text_length={len(result.text)}")

    # 생성 정보 포함 응답
    generation_info = GenerationInfo(
        mode=result.mode.value,
        model=result.model,
        user_prompt=result.user_prompt,
        system_prompt=result.system_prompt,
        full_prompt=result.full_prompt
    )

    # status가 Enum이면 .value, 문자열이면 그대로 사용
    status_value = block.status.value if hasattr(block.status, 'value') else block.status

    return GenerateTextResponse(
        id=block.id,
        project_id=block.project_id,
        index=block.index,
        text=block.text,
        keywords=block.keywords,
        status=status_value,
        created_at=block.created_at,
        updated_at=block.updated_at,
        generation_info=generation_info
    )
