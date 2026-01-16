"""
웹 검색 서비스

DuckDuckGo 검색을 사용하여 웹 검색 기능 제공
- Primary: duckduckgo-search 라이브러리 (더 나은 품질)
- Fallback: DuckDuckGo Instant Answer API
"""

import httpx
from typing import List, Dict, Optional
from app.utils.logger import logger


class WebSearchError(Exception):
    """웹 검색 실패 예외"""
    pass


async def search_web(query: str, max_results: int = 5) -> Dict[str, any]:
    """
    DuckDuckGo 검색으로 웹 페이지 검색

    Args:
        query: 검색어
        max_results: 최대 결과 수

    Returns:
        {
            "results": [{"title": "...", "snippet": "...", "url": "..."}],
            "source": "duckduckgo" | "duckduckgo-instant-answer"
        }
    """
    logger.info(f"웹 검색 시작: query={query}")

    # 1차 시도: duckduckgo-search 라이브러리 (더 나은 품질)
    try:
        from duckduckgo_search import DDGS

        logger.debug("duckduckgo-search 라이브러리 사용 시도")

        # 동기 API를 비동기 컨텍스트에서 실행
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=max_results))

        if search_results:
            results = []
            for item in search_results:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("body", ""),
                    "url": item.get("href", "")
                })

            logger.info(f"웹 검색 완료 (duckduckgo-search): {len(results)}개 결과")
            return {
                "results": results,
                "source": "duckduckgo"  # OpenAI API 웹 검색처럼 보이지 않도록
            }

    except ImportError:
        logger.warning("duckduckgo-search 라이브러리 없음, Instant Answer API로 fallback")
    except Exception as e:
        logger.warning(f"duckduckgo-search 실패: {e}, Instant Answer API로 fallback")

    # 2차 시도: DuckDuckGo Instant Answer API (fallback)
    try:
        logger.debug("DuckDuckGo Instant Answer API 사용 (fallback)")

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
                raise WebSearchError("검색 결과가 없습니다.")

            logger.info(f"웹 검색 완료 (Instant Answer API fallback): {len(results)}개 결과")
            return {
                "results": results[:max_results],
                "source": "duckduckgo-instant-answer"  # Fallback 명시
            }

    except Exception as e:
        logger.error(f"웹 검색 실패 (모든 방법 실패): {e}")
        raise WebSearchError(f"웹 검색 중 오류 발생: {str(e)}")
