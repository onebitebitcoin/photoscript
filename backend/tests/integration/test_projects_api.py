"""
Projects API 통합 테스트

테스트 대상:
- GET /projects - 프로젝트 목록 조회
- POST /projects - 프로젝트 생성
- GET /projects/{id} - 프로젝트 상세 조회
- DELETE /projects/{id} - 프로젝트 삭제
- POST /projects/{id}/blocks - 블록 추가
- POST /projects/{id}/blocks/merge - 블록 합치기
"""

class TestProjectsList:
    """프로젝트 목록 조회 테스트"""

    def test_list_projects_empty(self, client):
        """빈 프로젝트 목록 조회"""
        response = client.get("/api/v1/projects")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_projects_with_data(self, client):
        """프로젝트가 있을 때 목록 조회"""
        # 프로젝트 2개 생성
        client.post("/api/v1/projects", json={
            "script_raw": "첫 번째 스크립트",
            "title": "프로젝트 1"
        })
        client.post("/api/v1/projects", json={
            "script_raw": "두 번째 스크립트",
            "title": "프로젝트 2"
        })

        response = client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # 최신순 정렬
        assert data[0]["title"] == "프로젝트 2"
        assert data[1]["title"] == "프로젝트 1"


class TestProjectCreate:
    """프로젝트 생성 테스트"""

    def test_create_project_with_title(self, client):
        """제목 포함 프로젝트 생성"""
        response = client.post("/api/v1/projects", json={
            "script_raw": "테스트 스크립트 내용입니다.",
            "title": "테스트 프로젝트"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "테스트 프로젝트"
        assert data["script_raw"] == "테스트 스크립트 내용입니다."
        assert "id" in data
        assert "created_at" in data

    def test_create_project_without_title(self, client):
        """제목 없이 프로젝트 생성"""
        response = client.post("/api/v1/projects", json={
            "script_raw": "제목 없는 스크립트"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["title"] is None
        assert data["script_raw"] == "제목 없는 스크립트"

    def test_create_project_empty_script(self, client):
        """빈 스크립트는 에러"""
        response = client.post("/api/v1/projects", json={
            "script_raw": ""
        })

        assert response.status_code == 422  # Validation Error


class TestProjectGet:
    """프로젝트 상세 조회 테스트"""

    def test_get_project_success(self, client):
        """프로젝트 상세 조회 성공"""
        # 프로젝트 생성
        create_response = client.post("/api/v1/projects", json={
            "script_raw": "상세 조회 테스트",
            "title": "테스트"
        })
        project_id = create_response.json()["id"]

        # 조회
        response = client.get(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["title"] == "테스트"
        assert "blocks" in data

    def test_get_project_not_found(self, client):
        """존재하지 않는 프로젝트 조회"""
        response = client.get("/api/v1/projects/non-existent-id")

        assert response.status_code == 404


class TestProjectDelete:
    """프로젝트 삭제 테스트"""

    def test_delete_project_success(self, client):
        """프로젝트 삭제 성공"""
        # 프로젝트 생성
        create_response = client.post("/api/v1/projects", json={
            "script_raw": "삭제 테스트",
            "title": "삭제할 프로젝트"
        })
        project_id = create_response.json()["id"]

        # 삭제
        response = client.delete(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        assert response.json()["message"] == "프로젝트가 삭제되었습니다"

        # 삭제 확인
        get_response = client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404

    def test_delete_project_not_found(self, client):
        """존재하지 않는 프로젝트 삭제"""
        response = client.delete("/api/v1/projects/non-existent-id")

        assert response.status_code == 404


class TestBlockCreate:
    """블록 추가 테스트"""

    def test_create_block_success(self, client):
        """블록 추가 성공"""
        # 프로젝트 생성
        create_response = client.post("/api/v1/projects", json={
            "script_raw": "블록 추가 테스트",
            "title": "블록 테스트"
        })
        project_id = create_response.json()["id"]

        # 블록 추가
        response = client.post(f"/api/v1/projects/{project_id}/blocks", json={
            "text": "새로운 블록 텍스트",
            "keywords": ["키워드1", "키워드2"],
            "insert_at": 0
        })

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "새로운 블록 텍스트"
        assert data["keywords"] == ["키워드1", "키워드2"]
        assert data["index"] == 0

    def test_create_block_empty_text(self, client):
        """빈 텍스트 블록 추가 (허용)"""
        # 프로젝트 생성
        create_response = client.post("/api/v1/projects", json={
            "script_raw": "테스트",
            "title": "테스트"
        })
        project_id = create_response.json()["id"]

        # 빈 블록 추가
        response = client.post(f"/api/v1/projects/{project_id}/blocks", json={
            "text": "",
            "insert_at": 0
        })

        assert response.status_code == 200
        assert response.json()["text"] == ""

    def test_create_block_project_not_found(self, client):
        """존재하지 않는 프로젝트에 블록 추가"""
        response = client.post("/api/v1/projects/non-existent/blocks", json={
            "text": "테스트",
            "insert_at": 0
        })

        assert response.status_code == 404


class TestBlockMerge:
    """블록 합치기 테스트"""

    def test_merge_blocks_success(self, client, db_session):
        """블록 합치기 성공"""
        from app.models import Project, Block
        from app.models.block import BlockStatus

        # 프로젝트와 블록 직접 생성
        project = Project(
            title="합치기 테스트",
            script_raw="테스트 스크립트"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 블록 3개 생성
        blocks = []
        for i in range(3):
            block = Block(
                project_id=project.id,
                index=i,
                text=f"블록 {i+1} 텍스트",
                keywords=[f"키워드{i+1}"],
                status=BlockStatus.DRAFT
            )
            db_session.add(block)
            db_session.commit()
            db_session.refresh(block)
            blocks.append(block)

        # 첫 두 블록 합치기
        response = client.post(
            f"/api/v1/projects/{project.id}/blocks/merge",
            json={"block_ids": [blocks[0].id, blocks[1].id]}
        )

        assert response.status_code == 200
        data = response.json()
        assert "블록 1 텍스트" in data["text"]
        assert "블록 2 텍스트" in data["text"]

    def test_merge_non_adjacent_blocks_fail(self, client, db_session):
        """인접하지 않은 블록 합치기 실패"""
        from app.models import Project, Block
        from app.models.block import BlockStatus

        # 프로젝트와 블록 생성
        project = Project(
            title="테스트",
            script_raw="테스트"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 블록 3개 생성
        blocks = []
        for i in range(3):
            block = Block(
                project_id=project.id,
                index=i,
                text=f"블록 {i+1}",
                keywords=[],
                status=BlockStatus.DRAFT
            )
            db_session.add(block)
            db_session.commit()
            db_session.refresh(block)
            blocks.append(block)

        # 첫 번째와 세 번째 블록 합치기 (인접하지 않음)
        response = client.post(
            f"/api/v1/projects/{project.id}/blocks/merge",
            json={"block_ids": [blocks[0].id, blocks[2].id]}
        )

        assert response.status_code == 400
        assert "인접한 블록만" in response.json()["detail"]["message"]
