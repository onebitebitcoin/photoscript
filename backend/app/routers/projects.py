from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Project, Block, Asset, BlockAsset
from app.models.block import BlockStatus
from app.models.block_asset import ChosenBy
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectDetailResponse,
    GenerateOptions,
    GenerateResponse,
    BlockResponse
)
from app.schemas.project import BlockSummary, AssetSummary
from app.services import process_script, ScriptProcessingError, PexelsClient, match_assets_for_block
from app.config import get_settings
from app.utils.logger import logger

router = APIRouter()
settings = get_settings()


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreate,
    db: Session = Depends(get_db)
):
    """프로젝트 생성 (스크립트 저장)"""
    logger.info(f"프로젝트 생성 요청: title={request.title}, script_length={len(request.script_raw)}")

    # 스크립트 길이 검증
    if len(request.script_raw) > settings.max_script_length:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "스크립트가 너무 깁니다",
                "max_length": settings.max_script_length
            }
        )

    project = Project(
        title=request.title,
        script_raw=request.script_raw
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    logger.info(f"프로젝트 생성 완료: id={project.id}")
    return project


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """프로젝트 상세 조회 (블록 + 대표 에셋 포함)"""
    logger.info(f"프로젝트 조회: id={project_id}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    # 블록 정보 구성 (대표 에셋 포함)
    blocks_data = []
    for block in project.blocks:
        # 대표 에셋 조회
        primary_ba = db.query(BlockAsset).filter(
            BlockAsset.block_id == block.id,
            BlockAsset.is_primary == True
        ).first()

        primary_asset = None
        if primary_ba:
            asset = db.query(Asset).filter(Asset.id == primary_ba.asset_id).first()
            if asset:
                primary_asset = AssetSummary(
                    id=asset.id,
                    asset_type=asset.asset_type,
                    thumbnail_url=asset.thumbnail_url,
                    source_url=asset.source_url
                )

        blocks_data.append(BlockSummary(
            id=block.id,
            index=block.index,
            text=block.text,
            keywords=block.keywords,
            status=block.status,
            primary_asset=primary_asset
        ))

    return ProjectDetailResponse(
        id=project.id,
        title=project.title,
        script_raw=project.script_raw,
        created_at=project.created_at,
        updated_at=project.updated_at,
        blocks=blocks_data
    )


@router.post("/{project_id}/generate", response_model=GenerateResponse)
async def generate_visuals(
    project_id: str,
    options: GenerateOptions = None,
    db: Session = Depends(get_db)
):
    """LLM으로 의미론적 블록 분할 + 키워드 추출 + 에셋 매칭 실행"""
    logger.info(f"Generate 시작: project_id={project_id}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    # 옵션 설정
    if options is None:
        options = GenerateOptions()

    max_candidates = options.max_candidates_per_block or settings.max_candidates_per_block

    # 기존 블록/에셋 삭제
    db.query(Block).filter(Block.project_id == project_id).delete()
    db.commit()

    # Step 1: LLM으로 의미론적 분할 + 키워드 추출 (한 번에)
    logger.info("Step 1: LLM으로 스크립트 처리 (의미론적 분할 + 키워드 추출)")
    try:
        processed_blocks = await process_script(project.script_raw)
    except ScriptProcessingError as e:
        logger.error(f"스크립트 처리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": f"스크립트 처리 실패: {str(e)}"}
        )

    if not processed_blocks:
        raise HTTPException(
            status_code=400,
            detail={"message": "스크립트를 분할할 수 없습니다. 내용을 확인해주세요."}
        )

    # Pexels 클라이언트 초기화
    pexels_client = PexelsClient()

    # Step 2: 각 블록에 대해 에셋 매칭
    logger.info(f"Step 2: {len(processed_blocks)}개 블록 에셋 매칭 시작")

    for idx, block_data in enumerate(processed_blocks):
        logger.info(f"블록 {idx+1}/{len(processed_blocks)} 처리 중")

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
            logger.warning(f"블록 {idx+1}: 키워드 없음")
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
                    is_primary=(i == 0),  # 첫 번째가 대표
                    chosen_by=ChosenBy.AUTO
                )
                db.add(block_asset)

            block.status = BlockStatus.MATCHED
        else:
            block.status = BlockStatus.NO_RESULT

        db.commit()

    logger.info(f"Generate 완료: {len(processed_blocks)}개 블록 생성")

    return GenerateResponse(
        status="completed",
        message=f"{len(processed_blocks)}개 블록 생성 및 매칭 완료",
        blocks_count=len(processed_blocks)
    )


@router.get("/{project_id}/blocks", response_model=List[BlockResponse])
async def get_project_blocks(
    project_id: str,
    db: Session = Depends(get_db)
):
    """프로젝트의 모든 블록 조회"""
    logger.info(f"블록 목록 조회: project_id={project_id}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    return project.blocks
