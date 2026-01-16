"""
Blocks API 통합 테스트

테스트 대상:
- PUT /blocks/{id} - 블록 수정
- POST /blocks/{id}/split - 블록 나누기
- DELETE /blocks/{id} - 블록 삭제
"""

import pytest
from app.models import Project, Block
from app.models.block import BlockStatus


@pytest.fixture
def project_with_blocks(db_session):
    """테스트용 프로젝트와 블록 생성"""
    project = Project(
        title="테스트 프로젝트",
        script_raw="테스트 스크립트 내용"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    blocks = []
    for i in range(3):
        block = Block(
            project_id=project.id,
            index=i,
            text=f"블록 {i+1}의 텍스트 내용입니다. 충분히 긴 텍스트가 필요합니다.",
            keywords=[f"키워드{i+1}"],
            status=BlockStatus.DRAFT
        )
        db_session.add(block)
        db_session.commit()
        db_session.refresh(block)
        blocks.append(block)

    return project, blocks


class TestBlockUpdate:
    """블록 수정 테스트"""

    def test_update_block_text(self, client, project_with_blocks):
        """블록 텍스트 수정"""
        project, blocks = project_with_blocks
        block = blocks[0]

        response = client.put(f"/api/v1/blocks/{block.id}", json={
            "text": "수정된 텍스트"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "수정된 텍스트"
        assert data["status"].upper() == "DRAFT"  # 수정 후 DRAFT 상태

    def test_update_block_keywords(self, client, project_with_blocks):
        """블록 키워드 수정"""
        project, blocks = project_with_blocks
        block = blocks[0]

        response = client.put(f"/api/v1/blocks/{block.id}", json={
            "keywords": ["새키워드1", "새키워드2"]
        })

        assert response.status_code == 200
        data = response.json()
        assert data["keywords"] == ["새키워드1", "새키워드2"]

    def test_update_block_both(self, client, project_with_blocks):
        """블록 텍스트와 키워드 동시 수정"""
        project, blocks = project_with_blocks
        block = blocks[0]

        response = client.put(f"/api/v1/blocks/{block.id}", json={
            "text": "새 텍스트",
            "keywords": ["새키워드"]
        })

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "새 텍스트"
        assert data["keywords"] == ["새키워드"]

    def test_update_block_not_found(self, client):
        """존재하지 않는 블록 수정"""
        response = client.put("/api/v1/blocks/non-existent", json={
            "text": "테스트"
        })

        assert response.status_code == 404


class TestBlockSplit:
    """블록 나누기 테스트"""

    def test_split_block_success(self, client, project_with_blocks):
        """블록 나누기 성공"""
        project, blocks = project_with_blocks
        block = blocks[0]
        original_text = block.text

        # 텍스트 중간 위치에서 분할
        split_position = len(original_text) // 2

        response = client.post(f"/api/v1/blocks/{block.id}/split", json={
            "split_position": split_position
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["text"] == original_text[:split_position].strip()
        assert data[1]["text"] == original_text[split_position:].strip()

    def test_split_block_invalid_position_zero(self, client, project_with_blocks):
        """위치 0에서 분할 시도 (실패)"""
        project, blocks = project_with_blocks
        block = blocks[0]

        response = client.post(f"/api/v1/blocks/{block.id}/split", json={
            "split_position": 0
        })

        assert response.status_code == 422  # Validation error (ge=1)

    def test_split_block_invalid_position_end(self, client, project_with_blocks):
        """텍스트 끝에서 분할 시도 (실패)"""
        project, blocks = project_with_blocks
        block = blocks[0]

        response = client.post(f"/api/v1/blocks/{block.id}/split", json={
            "split_position": len(block.text)
        })

        assert response.status_code == 400

    def test_split_block_not_found(self, client):
        """존재하지 않는 블록 나누기"""
        response = client.post("/api/v1/blocks/non-existent/split", json={
            "split_position": 10
        })

        assert response.status_code == 404


class TestBlockDelete:
    """블록 삭제 테스트"""

    def test_delete_block_success(self, client, project_with_blocks):
        """블록 삭제 성공"""
        project, blocks = project_with_blocks
        block = blocks[1]  # 중간 블록 삭제

        response = client.delete(f"/api/v1/blocks/{block.id}")

        assert response.status_code == 200
        assert response.json()["message"] == "블록이 삭제되었습니다"

        # 삭제 후 프로젝트 조회해서 블록 수 확인
        project_response = client.get(f"/api/v1/projects/{project.id}")
        assert len(project_response.json()["blocks"]) == 2

    def test_delete_block_reindex(self, client, project_with_blocks, db_session):
        """블록 삭제 후 인덱스 재정렬 확인"""
        project, blocks = project_with_blocks

        # 첫 번째 블록 삭제
        client.delete(f"/api/v1/blocks/{blocks[0].id}")

        # 프로젝트 조회해서 인덱스 확인
        project_response = client.get(f"/api/v1/projects/{project.id}")
        remaining_blocks = project_response.json()["blocks"]

        # 인덱스가 0부터 재정렬되었는지 확인
        indices = [b["index"] for b in remaining_blocks]
        assert indices == [0, 1]

    def test_delete_block_not_found(self, client):
        """존재하지 않는 블록 삭제"""
        response = client.delete("/api/v1/blocks/non-existent")

        assert response.status_code == 404


class TestBlockAssets:
    """블록 에셋 조회 테스트"""

    def test_get_block_assets_empty(self, client, project_with_blocks):
        """에셋 없는 블록 조회"""
        project, blocks = project_with_blocks
        block = blocks[0]

        response = client.get(f"/api/v1/blocks/{block.id}/assets")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_block_assets_not_found(self, client):
        """존재하지 않는 블록의 에셋 조회"""
        response = client.get("/api/v1/blocks/non-existent/assets")

        assert response.status_code == 404
