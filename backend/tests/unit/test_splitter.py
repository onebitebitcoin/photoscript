from app.services.splitter import split_script, split_into_sentences


class TestSplitIntoSentences:
    """문장 분할 테스트"""

    def test_korean_sentences(self):
        """한국어 문장 분할"""
        text = "첫 번째 문장입니다. 두 번째 문장입니다. 세 번째 문장입니다."
        result = split_into_sentences(text)
        assert len(result) == 3
        assert result[0] == "첫 번째 문장입니다."

    def test_english_sentences(self):
        """영어 문장 분할"""
        text = "First sentence. Second sentence! Third sentence?"
        result = split_into_sentences(text)
        assert len(result) == 3

    def test_mixed_punctuation(self):
        """혼합 문장부호"""
        text = "질문이 있습니다? 네, 물론이죠! 그렇군요."
        result = split_into_sentences(text)
        assert len(result) == 3


class TestSplitScript:
    """스크립트 분할 테스트"""

    def test_split_by_empty_line(self):
        """빈 줄로 문단 분할"""
        script = "첫 번째 문단입니다.\n\n두 번째 문단입니다."
        result = split_script(script)
        assert len(result) == 2
        assert result[0] == "첫 번째 문단입니다."
        assert result[1] == "두 번째 문단입니다."

    def test_single_paragraph(self):
        """단일 문단"""
        script = "하나의 문단만 있는 스크립트입니다."
        result = split_script(script)
        assert len(result) == 1

    def test_long_paragraph_split(self):
        """긴 문단 분할"""
        # 600자 이상의 긴 문단 생성
        long_para = "이것은 매우 긴 문장입니다. " * 50
        result = split_script(long_para, max_length=500)
        # 모든 블록이 최대 길이 이하인지 확인
        for block in result:
            assert len(block) <= 500

    def test_empty_script(self):
        """빈 스크립트"""
        result = split_script("")
        assert len(result) == 0

    def test_whitespace_only(self):
        """공백만 있는 스크립트"""
        result = split_script("   \n\n   ")
        assert len(result) == 0

    def test_multiple_empty_lines(self):
        """여러 개의 빈 줄"""
        script = "첫 번째.\n\n\n\n두 번째."
        result = split_script(script)
        assert len(result) == 2

    def test_preserves_content(self):
        """내용 보존 확인"""
        script = "중요한 내용입니다.\n\n또 다른 중요한 내용입니다."
        result = split_script(script)
        assert "중요한 내용입니다." in result[0]
        assert "또 다른 중요한 내용입니다." in result[1]
