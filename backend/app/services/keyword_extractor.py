import json
from typing import List
from openai import AsyncOpenAI
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class KeywordExtractionError(Exception):
    """키워드 추출 실패 예외"""
    pass


async def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    OpenAI GPT를 사용하여 텍스트에서 검색용 키워드 추출

    Args:
        text: 키워드를 추출할 텍스트
        max_keywords: 추출할 최대 키워드 수

    Returns:
        영어 키워드 리스트

    Raises:
        KeywordExtractionError: 키워드 추출 실패 시
    """
    logger.info(f"키워드 추출 시작: {len(text)}자 텍스트")

    if not settings.openai_api_key:
        logger.error("OpenAI API 키가 설정되지 않음")
        raise KeywordExtractionError("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = f"""다음 텍스트에서 이미지/영상 검색에 적합한 영어 키워드 {max_keywords}개를 추출해주세요.

규칙:
- 구체적이고 시각적인 키워드 우선 (예: sunset, coffee shop, business meeting)
- 일반적인 단어 제외 (예: person, good, thing, idea)
- 모든 키워드는 영어 단어 또는 짧은 구문
- JSON 배열 형식으로만 반환 (다른 설명 없이)

텍스트:
{text}

응답 형식 예시: ["sunset", "beach", "silhouette", "ocean", "golden hour"]"""

    try:
        # Responses API 사용 (gpt-5-mini)
        response = await client.responses.create(
            model="gpt-5-mini",
            input=prompt
        )

        content = response.output_text.strip()
        logger.debug(f"OpenAI 응답: {content}")

        # JSON 파싱
        keywords = json.loads(content)

        if not isinstance(keywords, list):
            raise ValueError("응답이 리스트가 아님")

        if len(keywords) == 0:
            raise ValueError("추출된 키워드가 없음")

        keywords = [str(k).strip() for k in keywords if k][:max_keywords]
        logger.info(f"키워드 추출 완료: {keywords}")
        return keywords

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        raise KeywordExtractionError(f"키워드 추출 응답 파싱 실패: {e}")
    except Exception as e:
        logger.error(f"키워드 추출 실패: {e}")
        raise KeywordExtractionError(f"키워드 추출 실패: {e}")
