from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Project, Block, Asset, BlockAsset, QAVersion
from app.models.user import User
from app.models.block import BlockStatus
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
    BlockCreate,
    QAVersionResponse,
    QAVersionListItem,
    QAVersionUpdate
)
from app.schemas.project import BlockSummary, AssetSummary, QAScriptResponse, QAScriptRequest
from app.services import process_script, ScriptProcessingError, PexelsClient, match_assets_for_block, validate_and_correct_script, QAServiceError, QAVersionService
from app.services.asset_service import AssetService
from app.services.block_service import BlockService
from app.services.project_service import ProjectService
from app.errors import ProjectNotFoundError
from app.config import get_settings
from app.utils.logger import logger

router = APIRouter()
settings = get_settings()
asset_service = AssetService()
block_service = BlockService()
project_service = ProjectService()
qa_version_service = QAVersionService()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """프로젝트 목록 조회 (최신순, 로그인한 사용자 소유만)"""
    logger.info(f"프로젝트 목록 조회: user_id={current_user.id}")

    projects = project_service.get_projects(db, current_user.id)

    logger.info(f"프로젝트 목록 조회 완료: {len(projects)}개")
    return projects


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """프로젝트 삭제 (본인 소유만)"""
    logger.info(f"프로젝트 삭제 요청: id={project_id}, user_id={current_user.id}")

    try:
        project_service.delete_project(db, project_id, current_user.id)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": e.message})

    logger.info(f"프로젝트 삭제 완료: id={project_id}")
    return {"message": "프로젝트가 삭제되었습니다"}


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """프로젝트 생성 (스크립트 저장)"""
    logger.info(f"프로젝트 생성 요청: title={request.title}, user_id={current_user.id}")

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
        user_id=current_user.id,
        title=request.title,
        script_raw=request.script_raw
    )

    logger.info(f"프로젝트 생성 완료: id={project.id}")
    return project


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """프로젝트 상세 조회 (블록 + 대표 에셋 포함, 본인 소유만)"""
    logger.info(f"프로젝트 조회: id={project_id}, user_id={current_user.id}")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    # 블록 정보 구성 (대표 에셋 포함)
    blocks_data = []
    for block in project.blocks:
        # 대표 에셋 조회
        primary_ba = db.query(BlockAsset).filter(
            BlockAsset.block_id == block.id,
            BlockAsset.is_primary.is_(True)
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
            order=block.order,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """LLM으로 의미론적 블록 분할 + 키워드 추출 + 에셋 매칭 실행"""
    logger.info(f"Generate 시작: project_id={project_id}, user_id={current_user.id}")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
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

        # 블록 생성 (Fractional indexing)
        block = Block(
            project_id=project_id,
            order=float(idx + 1),  # 1.0, 2.0, 3.0, ...
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """프로젝트의 모든 블록 조회 (본인 소유만)"""
    logger.info(f"블록 목록 조회: project_id={project_id}, user_id={current_user.id}")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    return project.blocks


@router.post("/{project_id}/split", response_model=SplitResponse)
async def split_script(
    project_id: str,
    options: SplitOptions = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """스크립트를 LLM으로 의미론적 분할 + 키워드 추출 (에셋 매칭 없이)"""
    logger.info(f"Split 시작: project_id={project_id}, user_id={current_user.id}")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
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

    # 블록 생성 (DRAFT 상태) - Fractional indexing 사용
    blocks_data = []
    for idx, block_data in enumerate(processed_blocks):
        block = Block(
            project_id=project_id,
            order=float(idx + 1),  # 1.0, 2.0, 3.0, ...
            text=block_data["text"],
            keywords=block_data.get("keywords", []),
            status=BlockStatus.DRAFT
        )
        db.add(block)
        db.commit()
        db.refresh(block)

        blocks_data.append(BlockSummary(
            id=block.id,
            order=block.order,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """편집된 블록들에 대해 에셋 매칭 실행 (영상 우선)"""
    logger.info(f"Match 시작: project_id={project_id}, user_id={current_user.id}")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    # 블록 확인
    blocks = db.query(Block).filter(Block.project_id == project_id).order_by(Block.order).all()
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
    for idx, block in enumerate(blocks):
        logger.info(f"블록 {idx+1}/{len(blocks)} 처리 중")

        # 키워드가 없으면 NO_RESULT
        if not block.keywords:
            logger.warning(f"블록 {idx+1}: 키워드 없음")
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


@router.post("/{project_id}/blocks", response_model=BlockResponse)
async def create_block(
    project_id: str,
    request: BlockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """새 블록 추가 (본인 소유만)"""
    logger.info(f"블록 추가: project_id={project_id}, user_id={current_user.id}")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    new_block = block_service.create_block(
        db,
        project_id,
        text=request.text,
        keywords=request.keywords,
        order=request.order
    )

    logger.info(f"블록 추가 완료: block_id={new_block.id}, order={new_block.order}")
    return new_block


@router.post("/{project_id}/qa-script", response_model=QAScriptResponse)
async def qa_script_validation(
    project_id: str,
    request: QAScriptRequest = QAScriptRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """유튜브 스크립트 QA 검증 및 보정 (본인 소유만)"""
    logger.info(f"QA 검증 시작: project_id={project_id}, user_id={current_user.id}")

    # 1. 프로젝트 조회 및 소유권 확인
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    # 2. 최신 버전의 보정 스크립트가 있으면 사용, 없으면 원본 블록 사용
    latest_script = qa_version_service.get_latest_corrected_script(db, project_id)

    if latest_script:
        full_script = latest_script
        logger.info(f"최신 버전 스크립트 사용: {len(full_script)}자")
    else:
        # 블록들을 order 순으로 조회
        blocks = db.query(Block).filter(
            Block.project_id == project_id
        ).order_by(Block.order).all()

        if not blocks:
            raise HTTPException(
                status_code=400,
                detail={"message": "스크립트에 블록이 없습니다. 먼저 블록을 생성해주세요."}
            )

        # 블록 텍스트를 하나의 스크립트로 결합
        full_script = "\n\n".join([block.text for block in blocks])
        logger.info(f"원본 블록 스크립트 사용: {len(blocks)}개 블록, {len(full_script)}자")

    # 3. QA 서비스 호출 (추가 프롬프트 포함)
    try:
        qa_result = await validate_and_correct_script(
            full_script,
            additional_prompt=request.additional_prompt
        )
    except QAServiceError as e:
        logger.error(f"QA 검증 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": f"QA 검증 실패: {str(e)}"}
        )

    # 4. 검증 성공 시 자동으로 버전 저장
    try:
        qa_version_service.create_version(
            db=db,
            project_id=project_id,
            corrected_script=qa_result.corrected_script,
            model=qa_result.model
        )
        logger.info(f"QA 버전 자동 저장 완료: project_id={project_id}")
    except Exception as e:
        logger.warning(f"QA 버전 저장 실패 (경고만): {e}")

    logger.info(f"QA 검증 완료: project_id={project_id}")
    return qa_result


# ==========================================================================
# QA 버전 관리 API
# ==========================================================================

@router.get("/{project_id}/qa-versions", response_model=List[QAVersionListItem])
async def get_qa_versions(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """QA 버전 목록 조회 (스크립트 제외)"""
    logger.info(f"QA 버전 목록 조회: project_id={project_id}, user_id={current_user.id}")

    # 프로젝트 소유권 확인
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    versions = qa_version_service.get_versions(db, project_id)
    logger.info(f"QA 버전 목록 조회 완료: {len(versions)}개")
    return versions


@router.get("/{project_id}/qa-versions/{version_id}", response_model=QAVersionResponse)
async def get_qa_version(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """QA 버전 상세 조회 (스크립트 포함)"""
    logger.info(f"QA 버전 상세 조회: project_id={project_id}, version_id={version_id}")

    # 프로젝트 소유권 확인
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    version = qa_version_service.get_version_by_id(db, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(status_code=404, detail={"message": "버전을 찾을 수 없습니다"})

    logger.info(f"QA 버전 상세 조회 완료: version_id={version_id}")
    return version


@router.put("/{project_id}/qa-versions/{version_id}", response_model=QAVersionResponse)
async def update_qa_version(
    project_id: str,
    version_id: str,
    update_data: QAVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """QA 버전 메타데이터 수정 (이름, 메모)"""
    logger.info(f"QA 버전 수정: project_id={project_id}, version_id={version_id}")

    # 프로젝트 소유권 확인
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    # 버전 존재 및 소유권 확인
    version = qa_version_service.get_version_by_id(db, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(status_code=404, detail={"message": "버전을 찾을 수 없습니다"})

    # 수정
    updated_version = qa_version_service.update_version(
        db=db,
        version_id=version_id,
        version_name=update_data.version_name,
        memo=update_data.memo
    )

    logger.info(f"QA 버전 수정 완료: version_id={version_id}")
    return updated_version


@router.delete("/{project_id}/qa-versions/{version_id}")
async def delete_qa_version(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """QA 버전 삭제"""
    logger.info(f"QA 버전 삭제: project_id={project_id}, version_id={version_id}")

    # 프로젝트 소유권 확인
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail={"message": "프로젝트를 찾을 수 없습니다"})

    # 버전 존재 및 소유권 확인
    version = qa_version_service.get_version_by_id(db, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(status_code=404, detail={"message": "버전을 찾을 수 없습니다"})

    # 삭제
    success = qa_version_service.delete_version(db, version_id)
    if not success:
        raise HTTPException(status_code=500, detail={"message": "버전 삭제 실패"})

    logger.info(f"QA 버전 삭제 완료: version_id={version_id}")
    return {"message": "버전이 삭제되었습니다"}
