"""
웹 검색 서비스

DuckDuckGo 검색 API를 사용하여 웹 검색 기능 제공
"""

import httpx
from typing import List, Dict, Optional
from app.utils.logger import logger


class WebSearchError(Exception):
    """웹 검색 실패 예외"""
    pass


async def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    DuckDuckGo 검색으로 웹 페이지 검색

    Args:
        query: 검색어
        max_results: 최대 결과 수

    Returns:
        [{"title": "...", "snippet": "...", "url": "..."}]
    """
    logger.info(f"웹 검색 시작: query={query}")

    try:
        # DuckDuckGo Instant Answer API 사용
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1"
                }
            )
            response.raise_for_status()
            data = response.json()

            results = []

            # Abstract (요약)
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", "Summary"),
                    "snippet": data.get("Abstract"),
                    "url": data.get("AbstractURL", "")
                })

            # Related Topics
            for topic in data.get("RelatedTopics", [])[:max_results-1]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0],
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", "")
                    })

            if not results:
                logger.warning(f"검색 결과 없음: query={query}")
                return []

            logger.info(f"웹 검색 완료: {len(results)}개 결과")
            return results[:max_results]

    except Exception as e:
        logger.error(f"웹 검색 실패: {e}")
        raise WebSearchError(f"웹 검색 중 오류 발생: {str(e)}")
