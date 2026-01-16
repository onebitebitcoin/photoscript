"""
text_generator.py 유닛 테스트

테스트 대상:
- detect_mode(): 프롬프트 자동 모드 판단
- remove_source_references(): 출처/참고 제거
- is_url(): URL 유효성 검사
"""

import pytest
from app.services.text_generator import (
    detect_mode,
    remove_source_references,
    is_url,
    TextGenerationMode,
)


class TestDetectMode:
    """detect_mode() 함수 테스트"""

    def test_detect_link_mode_with_url_only(self):
        """URL만 있을 때 LINK 모드"""
        mode, extracted, guide = detect_mode("https://example.com/article")

        assert mode == TextGenerationMode.LINK
        assert extracted == "https://example.com/article"
        assert guide is None

    def test_detect_link_mode_with_url_and_guide(self):
        """URL + 가이드 텍스트가 있을 때 LINK 모드"""
        mode, extracted, guide = detect_mode("https://example.com 이 내용 참고해서 작성해줘")

        assert mode == TextGenerationMode.LINK
        assert extracted == "https://example.com"
        assert guide == "이 내용 참고해서 작성해줘"

    def test_detect_link_mode_with_guide_before_url(self):
        """가이드가 URL 앞에 있을 때도 LINK 모드"""
        mode, extracted, guide = detect_mode("이 링크 참고해서 https://example.com/page 작성해줘")

        assert mode == TextGenerationMode.LINK
        assert extracted == "https://example.com/page"
        assert "참고해서" in guide

    def test_detect_search_mode_with_검색해서(self):
        """'검색해서' 키워드로 SEARCH 모드"""
        mode, extracted, guide = detect_mode("AI 트렌드 검색해서 작성해줘")

        assert mode == TextGenerationMode.SEARCH
        assert extracted == "AI 트렌드"
        assert guide == "작성해줘"

    def test_detect_search_mode_with_찾아서(self):
        """'찾아서' 키워드로 SEARCH 모드"""
        mode, extracted, guide = detect_mode("최신 뉴스 찾아서 요약해줘")

        assert mode == TextGenerationMode.SEARCH
        assert extracted == "최신 뉴스"
        assert guide == "요약해줘"

    def test_detect_search_mode_with_알아봐서(self):
        """'알아봐서' 키워드로 SEARCH 모드"""
        mode, extracted, guide = detect_mode("파이썬 버전 알아봐서 알려줘")

        assert mode == TextGenerationMode.SEARCH
        assert extracted == "파이썬 버전"
        assert guide == "알려줘"

    def test_detect_search_mode_keyword_at_start(self):
        """검색 키워드가 문장 앞에 있을 때"""
        mode, extracted, guide = detect_mode("검색해서 AI 트렌드 관련 내용")

        assert mode == TextGenerationMode.SEARCH
        # 검색어가 없으면 가이드를 검색어로 사용
        assert extracted == "AI 트렌드 관련 내용"
        assert guide is None

    def test_detect_enhance_mode_simple_text(self):
        """일반 텍스트는 ENHANCE 모드"""
        mode, extracted, guide = detect_mode("위 내용을 더 자세히 설명해줘")

        assert mode == TextGenerationMode.ENHANCE
        assert extracted == "위 내용을 더 자세히 설명해줘"
        assert guide is None

    def test_detect_enhance_mode_with_expansion_request(self):
        """확장 요청도 ENHANCE 모드"""
        mode, extracted, guide = detect_mode("이 부분을 5문장으로 늘려줘")

        assert mode == TextGenerationMode.ENHANCE
        assert extracted == "이 부분을 5문장으로 늘려줘"
        assert guide is None

    def test_detect_mode_url_takes_priority_over_search(self):
        """URL이 있으면 검색 키워드가 있어도 LINK 모드"""
        mode, extracted, guide = detect_mode("https://example.com 검색해서 비교해줘")

        # URL이 있으므로 LINK 모드가 우선
        assert mode == TextGenerationMode.LINK
        assert extracted == "https://example.com"

    def test_detect_mode_strips_whitespace(self):
        """앞뒤 공백 제거"""
        mode, extracted, guide = detect_mode("   간단한 텍스트   ")

        assert mode == TextGenerationMode.ENHANCE
        assert extracted == "간단한 텍스트"


class TestRemoveSourceReferences:
    """remove_source_references() 함수 테스트"""

    def test_remove_source_line_korean(self):
        """한국어 '출처:' 줄 제거"""
        text = "내용입니다.\n출처: https://example.com"
        result = remove_source_references(text)

        assert "출처" not in result
        assert "example.com" not in result
        assert "내용입니다" in result

    def test_remove_reference_line_korean(self):
        """한국어 '참고:' 줄 제거"""
        text = "내용입니다.\n참고: https://example.com"
        result = remove_source_references(text)

        assert "참고" not in result
        assert "내용입니다" in result

    def test_remove_source_line_english(self):
        """영어 'Source:' 줄 제거"""
        text = "Content here.\nSource: https://example.com"
        result = remove_source_references(text)

        assert "Source" not in result
        assert "Content here" in result

    def test_remove_reference_line_english(self):
        """영어 'Reference:' 줄 제거"""
        text = "Content here.\nReference: https://example.com"
        result = remove_source_references(text)

        assert "Reference" not in result

    def test_remove_url_only_line(self):
        """URL만 있는 줄 제거"""
        text = "내용입니다.\nhttps://example.com\n마지막 줄"
        result = remove_source_references(text)

        assert "example.com" not in result
        assert "내용입니다" in result
        assert "마지막 줄" in result

    def test_remove_url_in_parentheses(self):
        """괄호 안 URL 제거"""
        text = "내용입니다 (https://example.com) 추가 내용"
        result = remove_source_references(text)

        assert "example.com" not in result
        assert "내용입니다" in result
        assert "추가 내용" in result

    def test_remove_inline_source(self):
        """인라인 출처 제거"""
        text = "내용입니다. 출처: https://example.com 여기까지"
        result = remove_source_references(text)

        assert "출처" not in result
        assert "example.com" not in result

    def test_preserve_text_without_sources(self):
        """출처 없는 텍스트는 그대로 유지"""
        text = "이것은 일반 텍스트입니다.\n여러 줄이 있어요."
        result = remove_source_references(text)

        assert result == text.rstrip()

    def test_handle_empty_text(self):
        """빈 텍스트 처리"""
        assert remove_source_references("") == ""
        assert remove_source_references(None) is None

    def test_remove_multiple_sources(self):
        """여러 출처 제거"""
        text = "내용1\n출처: https://a.com\n내용2\n참고: https://b.com\n끝"
        result = remove_source_references(text)

        assert "출처" not in result
        assert "참고" not in result
        assert "내용1" in result
        assert "내용2" in result
        assert "끝" in result

    def test_remove_source_with_colon_variations(self):
        """콜론 변형 처리 (: vs ：)"""
        text1 = "내용\n출처: https://example.com"
        text2 = "내용\n출처：https://example.com"

        result1 = remove_source_references(text1)
        result2 = remove_source_references(text2)

        assert "example.com" not in result1
        assert "example.com" not in result2

    def test_remove_inline_url_in_sentence(self):
        """문장 중간의 인라인 URL 제거"""
        text = "이 정보는 https://example.com/article 에서 가져왔습니다."
        result = remove_source_references(text)

        assert "example.com" not in result
        assert "이 정보는" in result
        assert "에서 가져왔습니다" in result

    def test_remove_multiple_inline_urls(self):
        """여러 인라인 URL 제거"""
        text = "첫 번째 https://a.com 그리고 https://b.com/path 두 번째"
        result = remove_source_references(text)

        assert "https://" not in result
        assert "첫 번째" in result
        assert "두 번째" in result

    def test_remove_url_in_brackets(self):
        """대괄호 안 URL 제거"""
        text = "참고 자료 [https://example.com/ref] 입니다"
        result = remove_source_references(text)

        assert "example.com" not in result
        assert "참고 자료" in result
        assert "입니다" in result

    def test_preserve_inline_urls_when_disabled(self):
        """인라인 URL 제거 비활성화 시 유지"""
        text = "링크는 https://example.com 입니다"
        result = remove_source_references(text, remove_inline_urls=False)

        # 인라인 URL은 유지되어야 함
        assert "https://example.com" in result

    def test_clean_multiple_spaces(self):
        """연속된 공백 정리"""
        text = "첫 번째   두 번째    세 번째"
        result = remove_source_references(text)

        # 연속된 공백이 하나로 정리
        assert "  " not in result


class TestIsUrl:
    """is_url() 함수 테스트"""

    def test_valid_https_url(self):
        """유효한 HTTPS URL"""
        assert is_url("https://example.com") is True
        assert is_url("https://example.com/path") is True
        assert is_url("https://example.com/path?query=1") is True

    def test_valid_http_url(self):
        """유효한 HTTP URL"""
        assert is_url("http://example.com") is True

    def test_url_with_port(self):
        """포트 포함 URL"""
        assert is_url("http://localhost:8000") is True
        assert is_url("https://example.com:443/path") is True

    def test_url_with_ip(self):
        """IP 주소 URL"""
        assert is_url("http://192.168.1.1") is True
        assert is_url("http://192.168.1.1:8080/api") is True

    def test_invalid_url_no_protocol(self):
        """프로토콜 없는 URL"""
        assert is_url("example.com") is False
        assert is_url("www.example.com") is False

    def test_invalid_url_text(self):
        """일반 텍스트"""
        assert is_url("이것은 텍스트입니다") is False
        assert is_url("not a url") is False

    def test_invalid_url_partial(self):
        """부분적인 URL"""
        assert is_url("https://") is False

    def test_url_with_whitespace(self):
        """공백 포함 URL (strip 처리)"""
        assert is_url("  https://example.com  ") is True


class TestBuildPromptFunctions:
    """프롬프트 빌드 함수 테스트 (간접 테스트)"""

    def test_detect_mode_preserves_korean_text(self):
        """한국어 텍스트가 올바르게 처리되는지 확인"""
        mode, extracted, guide = detect_mode("최신 AI 기술 트렌드에 대해 검색해서 5문장으로 작성해줘")

        assert mode == TextGenerationMode.SEARCH
        assert "AI" in extracted or "AI" in (guide or "")

    def test_detect_mode_handles_special_characters(self):
        """특수문자 처리"""
        mode, extracted, guide = detect_mode("https://example.com/path?q=한글&type=test")

        assert mode == TextGenerationMode.LINK
        assert "example.com" in extracted
