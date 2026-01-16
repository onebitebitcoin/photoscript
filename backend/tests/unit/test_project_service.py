"""
ProjectService 단위 테스트
"""

import pytest
from app.services.project_service import ProjectService
from app.models import Project, Block
from app.models.block import BlockStatus
from app.errors import ProjectNotFoundError


@pytest.fixture
def project_service():
    return ProjectService()


class TestGetProject:
    """get_project 테스트"""

    def test_get_existing_project(self, db_session, project_service):
        """존재하는 프로젝트 조회"""
        project = Project(title="테스트", script_raw="테스트 스크립트")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        result = project_service.get_project(db_session, project.id)
        assert result.id == project.id
        assert result.title == "테스트"

    def test_get_nonexistent_project_raises_error(self, db_session, project_service):
        """존재하지 않는 프로젝트 조회 시 에러"""
        with pytest.raises(ProjectNotFoundError):
            project_service.get_project(db_session, "non-existent-id")


class TestGetProjects:
    """get_projects 테스트"""

    def test_get_projects_empty(self, db_session, project_service):
        """빈 목록 조회"""
        result = project_service.get_projects(db_session)
        assert result == []

    def test_get_projects_ordered_by_created_at(self, db_session, project_service):
        """최신순 정렬 확인"""
        # 프로젝트 2개 생성
        p1 = Project(title="첫번째", script_raw="테스트")
        db_session.add(p1)
        db_session.commit()

        p2 = Project(title="두번째", script_raw="테스트")
        db_session.add(p2)
        db_session.commit()

        result = project_service.get_projects(db_session)
        assert len(result) == 2
        # 최신순이므로 두번째가 먼저
        assert result[0].title == "두번째"
        assert result[1].title == "첫번째"


class TestCreateProject:
    """create_project 테스트"""

    def test_create_project_with_title(self, db_session, project_service):
        """제목 있는 프로젝트 생성"""
        result = project_service.create_project(
            db_session,
            title="새 프로젝트",
            script_raw="스크립트 내용"
        )

        assert result.id is not None
        assert result.title == "새 프로젝트"
        assert result.script_raw == "스크립트 내용"

    def test_create_project_without_title(self, db_session, project_service):
        """제목 없는 프로젝트 생성"""
        result = project_service.create_project(
            db_session,
            title=None,
            script_raw="스크립트"
        )

        assert result.id is not None
        assert result.title is None


class TestDeleteProject:
    """delete_project 테스트"""

    def test_delete_project_success(self, db_session, project_service):
        """프로젝트 삭제 성공"""
        project = Project(title="삭제할 프로젝트", script_raw="테스트")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        project_id = project.id
        project_service.delete_project(db_session, project_id)

        # 삭제 확인
        result = db_session.query(Project).filter(Project.id == project_id).first()
        assert result is None

    def test_delete_project_with_blocks(self, db_session, project_service):
        """블록이 있는 프로젝트 삭제"""
        project = Project(title="테스트", script_raw="테스트")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 블록 추가
        block = Block(
            project_id=project.id,
            index=0,
            text="블록 텍스트",
            keywords=["키워드"],
            status=BlockStatus.DRAFT
        )
        db_session.add(block)
        db_session.commit()

        project_id = project.id
        project_service.delete_project(db_session, project_id)

        # 프로젝트와 블록 모두 삭제 확인
        assert db_session.query(Project).filter(Project.id == project_id).first() is None
        assert db_session.query(Block).filter(Block.project_id == project_id).first() is None

    def test_delete_nonexistent_project_raises_error(self, db_session, project_service):
        """존재하지 않는 프로젝트 삭제 시 에러"""
        with pytest.raises(ProjectNotFoundError):
            project_service.delete_project(db_session, "non-existent-id")
