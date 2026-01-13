import json
from typing import List
from openai import AsyncOpenAI
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


async def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    OpenAI GPT를 사용하여 텍스트에서 검색용 키워드 추출

    Args:
        text: 키워드를 추출할 텍스트
        max_keywords: 추출할 최대 키워드 수

    Returns:
        영어 키워드 리스트
    """
    logger.info(f"키워드 추출 시작: {len(text)}자 텍스트")

    if not settings.openai_api_key:
        logger.warning("OpenAI API 키가 설정되지 않음. 기본 키워드 반환")
        return ["scene", "background", "visual"]

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
        # Responses API 사용 (gpt-4o-mini)
        response = await client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )

        content = response.output_text.strip()
        logger.debug(f"OpenAI 응답: {content}")

        # JSON 파싱
        keywords = json.loads(content)

        if not isinstance(keywords, list):
            raise ValueError("응답이 리스트가 아님")

        keywords = [str(k).strip() for k in keywords if k][:max_keywords]
        logger.info(f"키워드 추출 완료: {keywords}")
        return keywords

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        return extract_fallback_keywords(text)
    except Exception as e:
        logger.error(f"키워드 추출 실패: {e}")
        return extract_fallback_keywords(text)


def extract_fallback_keywords(text: str) -> List[str]:
    """
    OpenAI 실패 시 간단한 폴백 키워드 추출
    """
    logger.info("폴백 키워드 추출 사용")

    # 간단한 키워드 추출: 긴 단어들 추출
    words = text.split()
    keywords = []

    for word in words:
        # 영어 단어만 추출
        clean = ''.join(c for c in word if c.isalpha())
        if len(clean) >= 4 and clean.isascii():
            keywords.append(clean.lower())

    # 중복 제거 및 상위 5개
    unique_keywords = list(dict.fromkeys(keywords))[:5]

    if not unique_keywords:
        unique_keywords = ["scene", "background", "visual"]

    logger.info(f"폴백 키워드: {unique_keywords}")
    return unique_keywords
