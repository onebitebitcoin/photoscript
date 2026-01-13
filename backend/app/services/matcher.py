from typing import List, Dict, Any
from app.services.pexels_client import PexelsClient
from app.utils.logger import logger


def calculate_relevance_score(keyword: str, asset: Dict[str, Any], video_priority: bool = False) -> float:
    """
    에셋의 관련성 점수 계산

    Args:
        keyword: 검색 키워드
        asset: 에셋 정보
        video_priority: True면 영상 우선, False면 이미지 우선

    Returns:
        관련성 점수 (0.0 ~ 2.0)
    """
    score = 1.0

    # 제목에 키워드 포함 시 가산점
    title = asset.get("title", "").lower()
    if keyword.lower() in title:
        score += 0.5

    # 영상/이미지 우선순위
    if video_priority:
        # 영상 우선
        if asset["asset_type"] == "VIDEO":
            score += 0.3
    else:
        # 이미지 우선 (기존 로직)
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
    max_candidates: int = 10,
    video_priority: bool = False
) -> List[Dict[str, Any]]:
    """
    블록에 대한 에셋 후보 검색 및 점수화

    Args:
        block_text: 블록 텍스트 (현재 미사용, 추후 확장용)
        keywords: 검색 키워드 리스트
        pexels_client: Pexels API 클라이언트
        max_candidates: 최대 후보 수
        video_priority: True면 영상 우선 검색

    Returns:
        점수순으로 정렬된 에셋 리스트
    """
    logger.info(f"에셋 매칭 시작: 키워드={keywords}, video_priority={video_priority}")

    all_assets = []

    if video_priority:
        # 영상 우선 검색: 영상 5개, 이미지 2개
        for keyword in keywords:
            # 영상 먼저 검색
            videos = await pexels_client.search_videos(keyword, per_page=5)
            for video in videos:
                video["score"] = calculate_relevance_score(keyword, video, video_priority=True)
                video["matched_keyword"] = keyword
                all_assets.append(video)

            # 영상이 부족하면 이미지로 보충
            photos = await pexels_client.search_photos(keyword, per_page=2)
            for photo in photos:
                photo["score"] = calculate_relevance_score(keyword, photo, video_priority=True)
                photo["matched_keyword"] = keyword
                all_assets.append(photo)
    else:
        # 이미지 우선 검색 (기존 로직)
        for keyword in keywords:
            photos = await pexels_client.search_photos(keyword, per_page=5)
            for photo in photos:
                photo["score"] = calculate_relevance_score(keyword, photo, video_priority=False)
                photo["matched_keyword"] = keyword
                all_assets.append(photo)

            videos = await pexels_client.search_videos(keyword, per_page=2)
            for video in videos:
                video["score"] = calculate_relevance_score(keyword, video, video_priority=False)
                video["matched_keyword"] = keyword
                all_assets.append(video)

    # 중복 제거
    unique_assets = deduplicate_by_url(all_assets)

    # 점수순 정렬
    sorted_assets = sorted(unique_assets, key=lambda x: x.get("score", 0), reverse=True)

    result = sorted_assets[:max_candidates]
    logger.info(f"에셋 매칭 완료: {len(result)}개 후보")

    return result
