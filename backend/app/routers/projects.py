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
    BlockResponse,
    SplitOptions,
    SplitResponse,
    MatchOptions,
    MatchResponse,
    BlockMergeRequest,
    BlockCreate
)
from app.schemas.project import BlockSummary, AssetSummary
from app.services import process_script, ScriptProcessingError, PexelsClient, match_assets_for_block
from app.services.asset_service import AssetService
from app.services.block_service import BlockService
from app.services.project_service import ProjectService
from app.errors import BlockMergeError, ProjectNotFoundError
from app.config import get_settings
from app.utils.logger import logger

router = APIRouter()
settings = get_settings()
asset_service = AssetService()
block_service = BlockService()
project_service = ProjectService()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db)
):
    """프로젝트 목록 조회 (최신순)"""
    logger.info("프로젝트 목록 조회")

    projects = project_service.get_projects(db)

    logger.info(f"프로젝트 목록 조회 완료: {len(projects)}개")
    return projects


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """프로젝트 삭제"""
    logger.info(f"프로젝트 삭제 요청: id={project_id}")

    try:
        project_service.delete_project(db, project_id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": e.message})

    logger.info(f"프로젝트 삭제 완료: id={project_id}")
    return {"message": "프로젝트가 삭제되었습니다"}


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

    project = project_service.create_project(
        db,
        title=request.title,
        script_raw=request.script_raw
    )

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

        # 에셋 저장 (AssetService 사용)
        if assets_data:
            asset_service.save_and_link_assets(db, block.id, assets_data, clear_existing=False)
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


@router.post("/{project_id}/split", response_model=SplitResponse)
async def split_script(
    project_id: str,
    options: SplitOptions = None,
    db: Session = Depends(get_db)
):
    """스크립트를 LLM으로 의미론적 분할 + 키워드 추출 (에셋 매칭 없이)"""
    logger.info(f"Split 시작: project_id={project_id}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    # 옵션 설정
    if options is None:
        options = SplitOptions()

    # 기존 블록 삭제
    db.query(Block).filter(Block.project_id == project_id).delete()
    db.commit()

    # LLM으로 의미론적 분할 + 키워드 추출
    logger.info("LLM으로 스크립트 처리 (의미론적 분할 + 키워드 추출)")
    try:
        processed_blocks = await process_script(
            project.script_raw,
            max_keywords=options.max_keywords
        )
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

    # 블록 생성 (DRAFT 상태)
    blocks_data = []
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

        blocks_data.append(BlockSummary(
            id=block.id,
            index=block.index,
            text=block.text,
            keywords=block.keywords,
            status=block.status,
            primary_asset=None
        ))

    logger.info(f"Split 완료: {len(processed_blocks)}개 블록 생성")

    return SplitResponse(
        status="split_completed",
        message=f"{len(processed_blocks)}개 블록으로 분할 완료",
        blocks_count=len(processed_blocks),
        blocks=blocks_data
    )


@router.post("/{project_id}/match", response_model=MatchResponse)
async def match_assets(
    project_id: str,
    options: MatchOptions = None,
    db: Session = Depends(get_db)
):
    """편집된 블록들에 대해 에셋 매칭 실행 (영상 우선)"""
    logger.info(f"Match 시작: project_id={project_id}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    # 블록 확인
    blocks = db.query(Block).filter(Block.project_id == project_id).order_by(Block.index).all()
    if not blocks:
        raise HTTPException(
            status_code=400,
            detail={"message": "매칭할 블록이 없습니다. 먼저 split을 실행해주세요."}
        )

    # 옵션 설정
    if options is None:
        options = MatchOptions()

    max_candidates = options.max_candidates_per_block or settings.max_candidates_per_block
    video_priority = options.video_priority if options.video_priority is not None else True

    # Pexels 클라이언트 초기화
    pexels_client = PexelsClient()

    # 각 블록에 대해 에셋 매칭
    logger.info(f"{len(blocks)}개 블록 에셋 매칭 시작 (video_priority={video_priority})")

    matched_count = 0
    for block in blocks:
        logger.info(f"블록 {block.index+1}/{len(blocks)} 처리 중")

        # 키워드가 없으면 NO_RESULT
        if not block.keywords:
            logger.warning(f"블록 {block.index+1}: 키워드 없음")
            asset_service.delete_block_assets(db, block.id)
            block.status = BlockStatus.NO_RESULT
            db.commit()
            continue

        # 에셋 매칭 (영상 우선)
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

        # 에셋 저장 (AssetService 사용)
        if assets_data:
            asset_service.save_and_link_assets(db, block.id, assets_data, clear_existing=True)
            block.status = BlockStatus.MATCHED
            matched_count += 1
        else:
            asset_service.delete_block_assets(db, block.id)
            block.status = BlockStatus.NO_RESULT

        db.commit()

    logger.info(f"Match 완료: {matched_count}/{len(blocks)}개 블록 매칭 성공")

    return MatchResponse(
        status="completed",
        message=f"{matched_count}/{len(blocks)}개 블록 매칭 완료",
        blocks_count=len(blocks)
    )


@router.post("/{project_id}/blocks/merge", response_model=BlockResponse)
async def merge_blocks(
    project_id: str,
    request: BlockMergeRequest,
    db: Session = Depends(get_db)
):
    """여러 블록을 하나로 합치기"""
    logger.info(f"블록 합치기: project_id={project_id}, block_ids={request.block_ids}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    try:
        merged_block = block_service.merge_blocks(db, project_id, request.block_ids)
    except BlockMergeError as e:
        raise HTTPException(status_code=400, detail={"message": e.message})

    logger.info(f"블록 합치기 완료: {len(request.block_ids)}개 -> 1개")
    return merged_block


@router.post("/{project_id}/blocks", response_model=BlockResponse)
async def create_block(
    project_id: str,
    request: BlockCreate,
    db: Session = Depends(get_db)
):
    """새 블록 추가"""
    logger.info(f"블록 추가: project_id={project_id}, insert_at={request.insert_at}")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    new_block = block_service.create_block(
        db,
        project_id,
        text=request.text,
        keywords=request.keywords,
        insert_at=request.insert_at
    )

    logger.info(f"블록 추가 완료: block_id={new_block.id}, index={new_block.index}")
    return new_block
