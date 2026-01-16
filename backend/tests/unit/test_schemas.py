"""
API 스키마 유닛 테스트

테스트 대상:
- GenerateTextRequest 스키마 검증
- BlockCreate 스키마 검증
- BlockUpdate 스키마 검증
"""

import pytest
from pydantic import ValidationError
from app.schemas.block import (
    GenerateTextRequest,
    BlockCreate,
    BlockUpdate,
    BlockSplitRequest,
    BlockMergeRequest,
    BlockSearchRequest,
)


class TestGenerateTextRequest:
    """GenerateTextRequest 스키마 테스트"""

    def test_valid_prompt(self):
        """유효한 프롬프트"""
        request = GenerateTextRequest(prompt="이 내용을 확장해줘")
        assert request.prompt == "이 내용을 확장해줘"

    def test_valid_prompt_with_url(self):
        """URL 포함 프롬프트"""
        request = GenerateTextRequest(prompt="https://example.com 참고해서 작성")
        assert "https://example.com" in request.prompt

    def test_valid_prompt_with_search_keyword(self):
        """검색 키워드 포함 프롬프트"""
        request = GenerateTextRequest(prompt="AI 트렌드 검색해서 작성해줘")
        assert "검색해서" in request.prompt

    def test_invalid_empty_prompt(self):
        """빈 프롬프트는 에러"""
        with pytest.raises(ValidationError) as exc_info:
            GenerateTextRequest(prompt="")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "min_length" in str(errors[0])

    def test_invalid_missing_prompt(self):
        """프롬프트 누락 시 에러"""
        with pytest.raises(ValidationError):
            GenerateTextRequest()


class TestBlockCreate:
    """BlockCreate 스키마 테스트"""

    def test_valid_block_create(self):
        """유효한 블록 생성 요청"""
        request = BlockCreate(
            text="테스트 텍스트",
            keywords=["키워드1", "키워드2"],
            insert_at=0
        )
        assert request.text == "테스트 텍스트"
        assert request.keywords == ["키워드1", "키워드2"]
        assert request.insert_at == 0

    def test_block_create_with_empty_text(self):
        """빈 텍스트로 블록 생성 (허용)"""
        request = BlockCreate(text="", insert_at=0)
        assert request.text == ""

    def test_block_create_default_values(self):
        """기본값 확인"""
        request = BlockCreate(insert_at=5)
        assert request.text == ""
        assert request.keywords == []

    def test_invalid_negative_insert_at(self):
        """음수 insert_at은 에러"""
        with pytest.raises(ValidationError):
            BlockCreate(insert_at=-1)


class TestBlockUpdate:
    """BlockUpdate 스키마 테스트"""

    def test_valid_text_update(self):
        """텍스트만 업데이트"""
        request = BlockUpdate(text="새로운 텍스트")
        assert request.text == "새로운 텍스트"
        assert request.keywords is None

    def test_valid_keywords_update(self):
        """키워드만 업데이트"""
        request = BlockUpdate(keywords=["new", "keywords"])
        assert request.keywords == ["new", "keywords"]
        assert request.text is None

    def test_valid_both_update(self):
        """텍스트와 키워드 모두 업데이트"""
        request = BlockUpdate(text="새 텍스트", keywords=["키워드"])
        assert request.text == "새 텍스트"
        assert request.keywords == ["키워드"]

    def test_empty_update_allowed(self):
        """빈 업데이트 허용"""
        request = BlockUpdate()
        assert request.text is None
        assert request.keywords is None


class TestBlockSplitRequest:
    """BlockSplitRequest 스키마 테스트"""

    def test_valid_split_position(self):
        """유효한 분할 위치"""
        request = BlockSplitRequest(split_position=10)
        assert request.split_position == 10

    def test_invalid_zero_position(self):
        """0 위치는 에러"""
        with pytest.raises(ValidationError):
            BlockSplitRequest(split_position=0)

    def test_invalid_negative_position(self):
        """음수 위치는 에러"""
        with pytest.raises(ValidationError):
            BlockSplitRequest(split_position=-5)


class TestBlockMergeRequest:
    """BlockMergeRequest 스키마 테스트"""

    def test_valid_merge_two_blocks(self):
        """2개 블록 합치기"""
        request = BlockMergeRequest(block_ids=["id1", "id2"])
        assert len(request.block_ids) == 2

    def test_valid_merge_multiple_blocks(self):
        """여러 블록 합치기"""
        request = BlockMergeRequest(block_ids=["id1", "id2", "id3", "id4"])
        assert len(request.block_ids) == 4

    def test_invalid_single_block(self):
        """1개 블록은 에러"""
        with pytest.raises(ValidationError):
            BlockMergeRequest(block_ids=["id1"])

    def test_invalid_too_many_blocks(self):
        """6개 이상 블록은 에러"""
        with pytest.raises(ValidationError):
            BlockMergeRequest(block_ids=["id1", "id2", "id3", "id4", "id5", "id6"])


class TestBlockSearchRequest:
    """BlockSearchRequest 스키마 테스트"""

    def test_valid_search_request(self):
        """유효한 검색 요청"""
        request = BlockSearchRequest(keyword="테스트 키워드")
        assert request.keyword == "테스트 키워드"
        assert request.video_priority is True  # 기본값

    def test_search_with_video_priority_false(self):
        """영상 우선 비활성화"""
        request = BlockSearchRequest(keyword="키워드", video_priority=False)
        assert request.video_priority is False

    def test_invalid_empty_keyword(self):
        """빈 키워드는 에러"""
        with pytest.raises(ValidationError):
            BlockSearchRequest(keyword="")

    def test_invalid_too_long_keyword(self):
        """너무 긴 키워드는 에러 (100자 초과)"""
        with pytest.raises(ValidationError):
            BlockSearchRequest(keyword="a" * 101)
