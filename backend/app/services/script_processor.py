"""
스크립트 의미론적 분할 및 키워드 추출 통합 서비스

LLM API 한 번 호출로:
1. 스크립트를 의미론적 블록으로 분할
2. 각 블록의 Pexels 검색용 영어 키워드 추출
"""

import json
from typing import List, Dict, Any
from openai import AsyncOpenAI
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class ScriptProcessingError(Exception):
    """스크립트 처리 실패 예외"""
    pass


async def process_script(script_raw: str, max_keywords: int = 5) -> List[Dict[str, Any]]:
    """
    LLM API 한 번 호출로 스크립트 의미론적 분할 + 키워드 추출

    Args:
        script_raw: 원본 스크립트 텍스트
        max_keywords: 블록당 최대 키워드 수

    Returns:
        [
            {"text": "블록1 텍스트", "keywords": ["keyword1", "keyword2", ...]},
            {"text": "블록2 텍스트", "keywords": ["keyword3", "keyword4", ...]},
            ...
        ]

    Raises:
        ScriptProcessingError: 스크립트 처리 실패 시
    """
    logger.info(f"스크립트 처리 시작: {len(script_raw)}자")

    if not settings.openai_api_key:
        logger.error("OpenAI API 키가 설정되지 않음")
        raise ScriptProcessingError("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

    if not script_raw or not script_raw.strip():
        logger.error("빈 스크립트")
        raise ScriptProcessingError("스크립트가 비어있습니다.")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = f"""다음 스크립트를 의미론적으로 분할하고, 각 블록에서 이미지/영상 검색용 영어 키워드를 추출해주세요.

## 규칙
1. **의미론적 분할**: 의미/맥락/장면이 바뀌는 지점에서 블록 분할
2. **블록 크기**: 각 블록은 최소 1문장, 최대 3-4문장 (자연스러운 단위)
3. **키워드 추출**: 각 블록마다 {max_keywords}개 이내의 시각적 영어 키워드 추출
   - 구체적이고 시각적인 키워드 우선 (예: sunset beach, coffee shop, business meeting)
   - 일반적인 단어 제외 (예: person, good, thing, idea)
   - Pexels 이미지 검색에 적합한 키워드
4. **JSON 배열 형식으로만 반환** (다른 설명 없이)

## 스크립트
{script_raw}

## 응답 형식 (JSON 배열만 반환)
[
  {{"text": "첫 번째 블록 텍스트", "keywords": ["keyword1", "keyword2", "keyword3"]}},
  {{"text": "두 번째 블록 텍스트", "keywords": ["keyword4", "keyword5"]}}
]"""

    try:
        logger.debug("OpenAI API 호출 시작")

        response = await client.responses.create(
            model="gpt-5-mini",
            input=prompt
        )

        content = response.output_text.strip()
        logger.debug(f"OpenAI 응답: {content[:500]}...")

        # JSON 파싱
        blocks = json.loads(content)

        if not isinstance(blocks, list):
            raise ValueError("응답이 리스트가 아님")

        if len(blocks) == 0:
            raise ValueError("분할된 블록이 없음")

        # 결과 검증 및 정규화
        result = []
        for i, block in enumerate(blocks):
            if not isinstance(block, dict):
                logger.warning(f"블록 {i}: dict가 아님, 건너뜀")
                continue

            text = block.get("text", "").strip()
            keywords = block.get("keywords", [])

            if not text:
                logger.warning(f"블록 {i}: 텍스트가 비어있음, 건너뜀")
                continue

            # 키워드 정규화
            if isinstance(keywords, list):
                keywords = [str(k).strip() for k in keywords if k][:max_keywords]
            else:
                keywords = []

            result.append({
                "text": text,
                "keywords": keywords
            })

        if not result:
            raise ValueError("유효한 블록이 없음")

        logger.info(f"스크립트 처리 완료: {len(result)}개 블록 생성")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        raise ScriptProcessingError(f"스크립트 처리 응답 파싱 실패: {e}")
    except Exception as e:
        logger.error(f"스크립트 처리 실패: {e}")
        raise ScriptProcessingError(f"스크립트 처리 실패: {e}")
