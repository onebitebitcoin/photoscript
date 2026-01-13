from typing import List, Dict, Any
from app.services.pexels_client import PexelsClient
from app.utils.logger import logger


def calculate_relevance_score(keyword: str, asset: Dict[str, Any]) -> float:
    """
    에셋의 관련성 점수 계산

    Args:
        keyword: 검색 키워드
        asset: 에셋 정보

    Returns:
        관련성 점수 (0.0 ~ 2.0)
    """
    score = 1.0

    # 제목에 키워드 포함 시 가산점
    title = asset.get("title", "").lower()
    if keyword.lower() in title:
        score += 0.5

    # 이미지를 영상보다 약간 선호 (로딩 속도)
    if asset["asset_type"] == "IMAGE":
        score += 0.1

    return score


def deduplicate_by_url(assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """URL 기준으로 중복 에셋 제거"""
    seen_urls = set()
    unique_assets = []

    for asset in assets:
        url = asset.get("source_url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_assets.append(asset)

    return unique_assets


async def match_assets_for_block(
    block_text: str,
    keywords: List[str],
    pexels_client: PexelsClient,
    max_candidates: int = 10
) -> List[Dict[str, Any]]:
    """
    블록에 대한 에셋 후보 검색 및 점수화

    Args:
        block_text: 블록 텍스트 (현재 미사용, 추후 확장용)
        keywords: 검색 키워드 리스트
        pexels_client: Pexels API 클라이언트
        max_candidates: 최대 후보 수

    Returns:
        점수순으로 정렬된 에셋 리스트
    """
    logger.info(f"에셋 매칭 시작: 키워드={keywords}")

    all_assets = []

    # 각 키워드로 검색
    for keyword in keywords:
        # 이미지 검색
        photos = await pexels_client.search_photos(keyword, per_page=5)
        for photo in photos:
            photo["score"] = calculate_relevance_score(keyword, photo)
            photo["matched_keyword"] = keyword
            all_assets.append(photo)

        # 영상 검색 (이미지보다 적게)
        videos = await pexels_client.search_videos(keyword, per_page=2)
        for video in videos:
            video["score"] = calculate_relevance_score(keyword, video)
            video["matched_keyword"] = keyword
            all_assets.append(video)

    # 중복 제거
    unique_assets = deduplicate_by_url(all_assets)

    # 점수순 정렬
    sorted_assets = sorted(unique_assets, key=lambda x: x.get("score", 0), reverse=True)

    result = sorted_assets[:max_candidates]
    logger.info(f"에셋 매칭 완료: {len(result)}개 후보")

    return result
