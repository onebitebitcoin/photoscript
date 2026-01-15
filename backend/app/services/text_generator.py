"""
블록 텍스트 자동 생성 서비스

URL이나 지시문을 기반으로 LLM이 블록용 텍스트를 생성
"""

import re
import httpx
from typing import Optional
from openai import AsyncOpenAI
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class TextGenerationError(Exception):
    """텍스트 생성 실패 예외"""
    pass


def is_url(text: str) -> bool:
    """URL인지 확인"""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(text.strip()))


async def fetch_url_content(url: str) -> str:
    """URL에서 텍스트 콘텐츠 추출"""
    logger.info(f"URL 콘텐츠 fetch: {url}")

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; PhotoScript/1.0)"
            })
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                # HTML에서 텍스트 추출 (간단한 처리)
                html = response.text
                # script, style 태그 제거
                html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
                # 태그 제거
                text = re.sub(r'<[^>]+>', ' ', html)
                # 여러 공백을 하나로
                text = re.sub(r'\s+', ' ', text).strip()
                # 최대 5000자
                return text[:5000]
            else:
                return response.text[:5000]

    except Exception as e:
        logger.error(f"URL fetch 실패: {e}")
        raise TextGenerationError(f"URL 콘텐츠를 가져올 수 없습니다: {str(e)}")


async def generate_block_text(prompt: str, existing_text: Optional[str] = None) -> str:
    """
    프롬프트를 기반으로 블록용 텍스트 생성

    Args:
        prompt: URL 또는 지시문
        existing_text: 기존 블록 텍스트 (있으면 참고)

    Returns:
        생성된 블록 텍스트

    Raises:
        TextGenerationError: 텍스트 생성 실패 시
    """
    logger.info(f"텍스트 생성 시작: prompt={prompt[:100]}...")

    if not settings.openai_api_key:
        logger.error("OpenAI API 키가 설정되지 않음")
        raise TextGenerationError("OpenAI API 키가 설정되지 않았습니다.")

    # URL이면 내용 fetch
    context = ""
    if is_url(prompt):
        context = await fetch_url_content(prompt)
        user_instruction = f"다음 URL의 내용을 기반으로 영상 스크립트 블록에 적합한 텍스트를 작성해주세요.\n\nURL 내용:\n{context}"
    else:
        user_instruction = prompt

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    system_prompt = """당신은 영상 스크립트 작성 전문가입니다.
사용자의 요청에 따라 영상 스크립트의 한 블록에 들어갈 텍스트를 작성합니다.

규칙:
1. 간결하고 명확한 문장으로 작성
2. 영상 나레이션에 적합한 톤
3. 1-3 문장 정도의 짧은 블록 텍스트
4. 시각적 설명이 가능한 내용 포함
5. 다른 설명 없이 블록 텍스트만 반환"""

    try:
        logger.debug("OpenAI API 호출 시작")

        response = await client.responses.create(
            model="gpt-5-mini",
            input=f"{system_prompt}\n\n사용자 요청:\n{user_instruction}"
        )

        generated_text = response.output_text.strip()
        logger.info(f"텍스트 생성 완료: {len(generated_text)}자")

        return generated_text

    except Exception as e:
        logger.error(f"텍스트 생성 실패: {e}")
        raise TextGenerationError(f"텍스트 생성 실패: {str(e)}")
