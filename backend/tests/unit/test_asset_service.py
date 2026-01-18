"""
AssetService 단위 테스트
"""

import pytest
from app.services.asset_service import AssetService
from app.models import Block, Project, BlockAsset
from app.models.block import BlockStatus
from app.models.block_asset import ChosenBy
from app.errors import AssetSaveError, AssetNotFoundError


@pytest.fixture
def asset_service():
    return AssetService()


@pytest.fixture
def sample_asset_data():
    return {
        "provider": "pexels",
        "asset_type": "IMAGE",
        "source_url": "https://example.com/image.jpg",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "title": "Test Image",
        "license": "Pexels License",
        "meta": {"width": 1920, "height": 1080}
    }


@pytest.fixture
def project_with_block(db_session):
    """테스트용 프로젝트와 블록"""
    project = Project(
        title="테스트 프로젝트",
        script_raw="테스트"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    block = Block(
        project_id=project.id,
        index=0,
        text="테스트 블록",
        keywords=["test"],
        status=BlockStatus.DRAFT
    )
    db_session.add(block)
    db_session.commit()
    db_session.refresh(block)

    return project, block


class TestGetOrCreateAsset:
    """get_or_create_asset 테스트"""

    def test_create_new_asset(self, db_session, asset_service, sample_asset_data):
        """새 에셋 생성"""
        asset = asset_service.get_or_create_asset(db_session, sample_asset_data)

        assert asset.id is not None
        assert asset.source_url == sample_asset_data["source_url"]
        assert asset.provider == "pexels"
        assert asset.asset_type == "IMAGE"

    def test_get_existing_asset(self, db_session, asset_service, sample_asset_data):
        """기존 에셋 조회"""
        # 첫 번째 생성
        asset1 = asset_service.get_or_create_asset(db_session, sample_asset_data)

        # 같은 URL로 다시 호출
        asset2 = asset_service.get_or_create_asset(db_session, sample_asset_data)

        assert asset1.id == asset2.id

    def test_missing_source_url_raises_error(self, db_session, asset_service):
        """source_url 없으면 에러"""
        with pytest.raises(AssetSaveError):
            asset_service.get_or_create_asset(db_session, {"provider": "pexels"})


class TestSaveAndLinkAssets:
    """save_and_link_assets 테스트"""

    def test_save_multiple_assets(self, db_session, asset_service, project_with_block):
        """여러 에셋 저장 및 연결"""
        project, block = project_with_block

        assets_data = [
            {
                "provider": "pexels",
                "asset_type": "IMAGE",
                "source_url": "https://example.com/image1.jpg",
                "thumbnail_url": "https://example.com/thumb1.jpg",
                "score": 0.9
            },
            {
                "provider": "pexels",
                "asset_type": "IMAGE",
                "source_url": "https://example.com/image2.jpg",
                "thumbnail_url": "https://example.com/thumb2.jpg",
                "score": 0.8
            }
        ]

        block_assets = asset_service.save_and_link_assets(
            db_session, block.id, assets_data
        )

        assert len(block_assets) == 2
        assert block_assets[0].is_primary is True  # 첫 번째가 대표
        assert block_assets[1].is_primary is False

    def test_clear_existing_assets(self, db_session, asset_service, project_with_block):
        """기존 에셋 삭제 후 새로 연결"""
        project, block = project_with_block

        # 첫 번째 에셋 연결
        first_assets = [
            {
                "provider": "pexels",
                "asset_type": "IMAGE",
                "source_url": "https://example.com/old.jpg",
                "thumbnail_url": "https://example.com/old_thumb.jpg"
            }
        ]
        asset_service.save_and_link_assets(db_session, block.id, first_assets)

        # 새 에셋으로 교체
        new_assets = [
            {
                "provider": "pexels",
                "asset_type": "IMAGE",
                "source_url": "https://example.com/new.jpg",
                "thumbnail_url": "https://example.com/new_thumb.jpg"
            }
        ]
        asset_service.save_and_link_assets(
            db_session, block.id, new_assets, clear_existing=True
        )

        # 블록에 연결된 에셋은 1개만
        all_links = db_session.query(BlockAsset).filter(
            BlockAsset.block_id == block.id
        ).all()
        assert len(all_links) == 1


class TestAddAssetToBlock:
    """add_asset_to_block 테스트"""

    def test_add_single_asset(self, db_session, asset_service, project_with_block, sample_asset_data):
        """단일 에셋 추가"""
        project, block = project_with_block

        block_asset = asset_service.add_asset_to_block(
            db_session, block.id, sample_asset_data
        )

        assert block_asset is not None
        assert block_asset.block_id == block.id

    def test_skip_duplicate_asset(self, db_session, asset_service, project_with_block, sample_asset_data):
        """중복 에셋 스킵"""
        project, block = project_with_block

        # 첫 번째 추가
        ba1 = asset_service.add_asset_to_block(db_session, block.id, sample_asset_data)
        assert ba1 is not None

        # 같은 에셋 다시 추가 시도
        ba2 = asset_service.add_asset_to_block(db_session, block.id, sample_asset_data)
        assert ba2 is None


class TestSetPrimaryAsset:
    """set_primary_asset 테스트"""

    def test_set_primary_success(self, db_session, asset_service, project_with_block):
        """대표 에셋 설정 성공"""
        project, block = project_with_block

        # 에셋 2개 추가
        assets_data = [
            {
                "provider": "pexels",
                "asset_type": "IMAGE",
                "source_url": "https://example.com/a.jpg",
                "thumbnail_url": "https://example.com/a_thumb.jpg"
            },
            {
                "provider": "pexels",
                "asset_type": "IMAGE",
                "source_url": "https://example.com/b.jpg",
                "thumbnail_url": "https://example.com/b_thumb.jpg"
            }
        ]
        block_assets = asset_service.save_and_link_assets(db_session, block.id, assets_data)

        # 두 번째 에셋을 대표로 설정
        second_asset_id = block_assets[1].asset_id
        result = asset_service.set_primary_asset(db_session, block.id, second_asset_id)

        assert result.is_primary is True
        assert result.chosen_by == ChosenBy.USER

        # 첫 번째 에셋은 대표 해제
        first_ba = db_session.query(BlockAsset).filter(
            BlockAsset.block_id == block.id,
            BlockAsset.asset_id == block_assets[0].asset_id
        ).first()
        assert first_ba.is_primary is False

    def test_set_primary_asset_not_found(self, db_session, asset_service, project_with_block):
        """없는 에셋을 대표로 설정 시 에러"""
        project, block = project_with_block

        with pytest.raises(AssetNotFoundError):
            asset_service.set_primary_asset(db_session, block.id, "non-existent-id")


class TestDeleteBlockAssets:
    """delete_block_assets 테스트"""

    def test_delete_all_assets(self, db_session, asset_service, project_with_block, sample_asset_data):
        """블록의 모든 에셋 삭제"""
        project, block = project_with_block

        # 에셋 추가
        asset_service.add_asset_to_block(db_session, block.id, sample_asset_data)

        # 삭제
        deleted_count = asset_service.delete_block_assets(db_session, block.id)

        assert deleted_count == 1

        # 확인
        links = db_session.query(BlockAsset).filter(
            BlockAsset.block_id == block.id
        ).all()
        assert len(links) == 0
