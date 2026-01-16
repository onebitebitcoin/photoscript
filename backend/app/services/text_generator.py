"""
블록 텍스트 자동 생성 서비스

URL이나 지시문을 기반으로 LLM이 블록용 텍스트를 생성
"""

import re
import httpx
from enum import Enum
from typing import Optional, Dict
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class TextGenerationMode(str, Enum):
    """텍스트 생성 모드"""
    LINK = "link"
    ENHANCE = "enhance"
    SEARCH = "search"


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


def detect_mode(prompt: str) -> tuple[TextGenerationMode, str, Optional[str]]:
    """
    프롬프트를 분석하여 자동으로 모드를 판단

    Returns:
        (mode, extracted_prompt, user_guide)
        - mode: 판단된 모드
        - extracted_prompt: URL 또는 검색어 (해당하는 경우)
        - user_guide: 사용자 가이드 (추가 지시사항)
    """
    prompt = prompt.strip()

    # 1. URL 패턴 확인 (URL이 포함되어 있으면 LINK 모드)
    url_match = re.search(r'(https?://[^\s]+)', prompt)
    if url_match:
        url = url_match.group(1)
        # URL 제거 후 남은 텍스트를 가이드로 사용
        user_guide = re.sub(r'https?://[^\s]+', '', prompt).strip()
        logger.info(f"자동 모드 판단: LINK (URL={url}, guide={user_guide or 'None'})")
        return (TextGenerationMode.LINK, url, user_guide or None)

    # 2. 검색 키워드 확인
    search_keywords = ['검색해서', '찾아서', '검색해줘', '찾아줘', '알아봐서', '알아봐줘']
    for kw in search_keywords:
        if kw in prompt:
            idx = prompt.find(kw)
            # 키워드 앞부분이 검색어, 뒷부분이 가이드
            search_query = prompt[:idx].strip()
            user_guide = prompt[idx + len(kw):].strip()

            # 검색어가 없으면 가이드를 검색어로 사용
            if not search_query:
                search_query = user_guide
                user_guide = None

            logger.info(f"자동 모드 판단: SEARCH (query={search_query}, guide={user_guide or 'None'})")
            return (TextGenerationMode.SEARCH, search_query, user_guide)

    # 3. 그 외: ENHANCE 모드 (입력 전체가 가이드)
    logger.info(f"자동 모드 판단: ENHANCE (guide={prompt[:50]}...)")
    return (TextGenerationMode.ENHANCE, prompt, None)


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


async def get_block_context(block_id: str, db: Session) -> Dict[str, Optional[str]]:
    """
    위/아래 블록 텍스트 조회

    Args:
        block_id: 현재 블록 ID
        db: DB 세션

    Returns:
        {"above": "...", "below": "...", "current_index": N}
    """
    from app.models import Block

    block = db.query(Block).filter(Block.id == block_id).first()
    if not block:
        logger.warning(f"블록을 찾을 수 없음: block_id={block_id}")
        return {"above": None, "below": None, "current_index": 0}

    # 위 블록
    above_block = db.query(Block).filter(
        Block.project_id == block.project_id,
        Block.index == block.index - 1
    ).first()

    # 아래 블록
    below_block = db.query(Block).filter(
        Block.project_id == block.project_id,
        Block.index == block.index + 1
    ).first()

    logger.info(f"블록 컨텍스트 조회: block_id={block_id}, has_above={above_block is not None}, has_below={below_block is not None}")

    return {
        "above": above_block.text if above_block else None,
        "below": below_block.text if below_block else None,
        "current_index": block.index
    }


def build_link_prompt(url_content: str, user_guide: str, context: Dict) -> str:
    """링크 모드 프롬프트 생성"""
    parts = []

    if context["above"]:
        parts.append(f"[이전 블록]\n{context['above']}\n")

    if context["below"]:
        parts.append(f"[다음 블록]\n{context['below']}\n")

    parts.append(f"[URL에서 가져온 참고 내용]\n{url_content}\n")

    if user_guide:
        parts.append(f"[사용자 요청]\n{user_guide}\n")

    parts.append("""[작성 지시]
위 URL 참고 내용을 바탕으로, 이전 블록과 다음 블록의 내용과 자연스럽게 이어지는 스크립트를 작성해주세요.
- 입니다체(존댓말)로 작성
- 1-3 문장의 간결한 블록 텍스트만 반환
- 다른 설명 없이 스크립트 내용만 출력
- 스크립트 마지막에 줄바꿈 후 "출처: (URL 또는 사이트명)" 형식으로 출처 표시""")

    return "\n".join(parts)


def build_enhance_prompt(user_guide: str, context: Dict) -> str:
    """보완 모드 프롬프트 생성"""
    parts = []

    if context["above"]:
        parts.append(f"[이전 블록]\n{context['above']}\n")

    if context["below"]:
        parts.append(f"[다음 블록]\n{context['below']}\n")

    parts.append(f"[사용자 요청]\n{user_guide}\n")

    parts.append("""[작성 지시]
위 사용자 요청을 바탕으로, 이전 블록과 다음 블록의 내용과 자연스럽게 이어지는 스크립트를 작성해주세요.
- 입니다체(존댓말)로 작성
- 1-3 문장의 간결한 블록 텍스트만 반환
- 다른 설명 없이 스크립트 내용만 출력""")

    return "\n".join(parts)


def build_search_prompt(search_query: str, user_guide: str, context: Dict) -> str:
    """검색 모드 프롬프트 생성 (OpenAI web_search 도구 사용)"""
    parts = []

    if context["above"]:
        parts.append(f"[이전 블록]\n{context['above']}\n")

    if context["below"]:
        parts.append(f"[다음 블록]\n{context['below']}\n")

    parts.append(f"[검색 키워드]\n{search_query}\n")

    if user_guide:
        parts.append(f"[사용자 요청]\n{user_guide}\n")

    parts.append("""[작성 지시]
위 검색 키워드로 웹 검색한 결과를 바탕으로, 이전 블록과 다음 블록의 내용과 자연스럽게 이어지는 스크립트를 작성해주세요.
- 입니다체(존댓말)로 작성
- 1-3 문장의 간결한 블록 텍스트만 반환
- 다른 설명 없이 스크립트 내용만 출력
- 스크립트 마지막에 줄바꿈 후 "출처: (참고한 URL 또는 사이트명)" 형식으로 출처 표시""")

    return "\n".join(parts)


async def generate_block_text(
    mode: TextGenerationMode,
    prompt: str,
    user_guide: Optional[str],
    block_id: str,
    db: Session,
    existing_text: Optional[str] = None
) -> str:
    """
    모드별 블록 텍스트 생성

    Args:
        mode: 생성 모드 (link/enhance/search)
        prompt: URL 또는 검색어
        user_guide: 사용자 가이드 (강화/반박 등)
        block_id: 블록 ID (컨텍스트 조회용)
        db: DB 세션
        existing_text: 기존 블록 텍스트

    Returns:
        생성된 블록 텍스트

    Raises:
        TextGenerationError: 텍스트 생성 실패 시
    """
    logger.info(f"텍스트 생성 시작: mode={mode}, prompt={prompt[:50]}...")

    # OpenAI API 키 확인
    if not settings.openai_api_key:
        logger.error("OpenAI API 키가 설정되지 않음")
        raise TextGenerationError("OpenAI API 키가 설정되지 않았습니다.")

    # 위/아래 블록 컨텍스트 조회
    context = await get_block_context(block_id, db)

    # 모드별 프롬프트 생성
    if mode == TextGenerationMode.LINK:
        if not is_url(prompt):
            raise TextGenerationError("링크 모드에서는 유효한 URL을 입력해야 합니다.")
        url_content = await fetch_url_content(prompt)
        user_instruction = build_link_prompt(url_content, user_guide or "", context)

    elif mode == TextGenerationMode.ENHANCE:
        # ENHANCE 모드에서는 prompt가 가이드 역할 (프론트엔드 호환)
        guide = user_guide or prompt
        if not guide:
            raise TextGenerationError("보완 모드에서는 가이드를 입력해야 합니다.")
        user_instruction = build_enhance_prompt(guide, context)

    elif mode == TextGenerationMode.SEARCH:
        # OpenAI web_search 도구를 사용하여 검색 + 텍스트 생성
        user_instruction = build_search_prompt(prompt, user_guide or "", context)

        # SEARCH 모드는 web_search 도구와 함께 별도로 호출
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        search_system_prompt = """당신은 영상 스크립트 작성 전문가입니다.
웹 검색을 통해 최신 정보를 찾아, 이전/다음 블록과 자연스럽게 이어지는 영상 스크립트를 작성합니다.

규칙:
1. 입니다체(존댓말)로 작성
2. 간결하고 명확한 1-3 문장
3. 영상 나레이션에 적합한 톤
4. 이전/다음 블록과 논리적 흐름 유지
5. 다른 설명 없이 스크립트 텍스트만 반환"""

        try:
            logger.debug("OpenAI API 호출 시작 (web_search 모드)")
            logger.debug(f"Search query: {prompt}")

            response = await client.responses.create(
                model="gpt-5-mini",
                tools=[{"type": "web_search"}],
                input=[
                    {"role": "system", "content": search_system_prompt},
                    {"role": "user", "content": user_instruction}
                ]
            )

            generated_text = response.output_text.strip()
            logger.info(f"텍스트 생성 완료 (web_search): {len(generated_text)}자")

            return generated_text

        except Exception as e:
            logger.error(f"텍스트 생성 실패 (web_search): error={str(e)}")
            raise TextGenerationError(f"웹 검색 텍스트 생성 실패: {str(e)}")

    else:
        raise TextGenerationError(f"지원하지 않는 모드: {mode}")

    # LLM 호출
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    system_prompt = """당신은 영상 스크립트 작성 전문가입니다.
사용자의 요청을 바탕으로 이전/다음 블록과 자연스럽게 이어지는 영상 스크립트를 작성합니다.

규칙:
1. 입니다체(존댓말)로 작성
2. 간결하고 명확한 1-3 문장
3. 영상 나레이션에 적합한 톤
4. 이전/다음 블록과 논리적 흐름 유지
5. 다른 설명 없이 스크립트 텍스트만 반환"""

    try:
        logger.debug("OpenAI API 호출 시작")
        logger.debug(f"User instruction: {user_instruction[:200]}...")

        response = await client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_instruction}
            ]
        )

        generated_text = response.output_text.strip()
        logger.info(f"텍스트 생성 완료: {len(generated_text)}자, mode={mode}")

        return generated_text

    except Exception as e:
        logger.error(f"텍스트 생성 실패: mode={mode}, error={str(e)}")
        raise TextGenerationError(f"텍스트 생성 실패: {str(e)}")


async def generate_block_text_auto(
    prompt: str,
    block_id: str,
    db: Session,
    existing_text: Optional[str] = None
) -> tuple[str, TextGenerationMode]:
    """
    프롬프트를 자동 분석하여 적절한 모드로 블록 텍스트 생성

    Args:
        prompt: 사용자 입력 프롬프트 (URL, 검색어, 또는 지시문)
        block_id: 블록 ID (컨텍스트 조회용)
        db: DB 세션
        existing_text: 기존 블록 텍스트

    Returns:
        (생성된 텍스트, 사용된 모드)

    Raises:
        TextGenerationError: 텍스트 생성 실패 시
    """
    # 자동 모드 판단
    mode, extracted_prompt, user_guide = detect_mode(prompt)

    logger.info(f"자동 텍스트 생성 시작: detected_mode={mode}, prompt={extracted_prompt[:50]}...")

    # 기존 generate_block_text 호출
    generated_text = await generate_block_text(
        mode=mode,
        prompt=extracted_prompt,
        user_guide=user_guide,
        block_id=block_id,
        db=db,
        existing_text=existing_text
    )

    return generated_text, mode
