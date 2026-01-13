from typing import List, Dict, Any, Optional
import httpx
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class PexelsClient:
    """Pexels API 클라이언트"""

    BASE_URL = "https://api.pexels.com/v1"
    VIDEO_URL = "https://api.pexels.com/videos"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.pexels_api_key
        self.headers = {"Authorization": self.api_key}

    async def search_photos(self, query: str, per_page: int = 10) -> List[Dict[str, Any]]:
        """
        Pexels 이미지 검색

        Args:
            query: 검색어
            per_page: 결과 수

        Returns:
            파싱된 이미지 정보 리스트
        """
        if not self.api_key:
            logger.warning("Pexels API 키가 설정되지 않음")
            return []

        logger.info(f"Pexels 이미지 검색: '{query}', per_page={per_page}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search",
                    params={"query": query, "per_page": per_page},
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                photos = [self._parse_photo(p) for p in data.get("photos", [])]
                logger.info(f"Pexels 이미지 검색 완료: {len(photos)}개 결과")
                return photos

        except httpx.HTTPStatusError as e:
            logger.error(f"Pexels API HTTP 에러: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Pexels 이미지 검색 실패: {e}")
            return []

    async def search_videos(self, query: str, per_page: int = 5) -> List[Dict[str, Any]]:
        """
        Pexels 영상 검색

        Args:
            query: 검색어
            per_page: 결과 수

        Returns:
            파싱된 영상 정보 리스트
        """
        if not self.api_key:
            logger.warning("Pexels API 키가 설정되지 않음")
            return []

        logger.info(f"Pexels 영상 검색: '{query}', per_page={per_page}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.VIDEO_URL}/search",
                    params={"query": query, "per_page": per_page},
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                videos = [self._parse_video(v) for v in data.get("videos", [])]
                logger.info(f"Pexels 영상 검색 완료: {len(videos)}개 결과")
                return videos

        except httpx.HTTPStatusError as e:
            logger.error(f"Pexels API HTTP 에러: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Pexels 영상 검색 실패: {e}")
            return []

    def _parse_photo(self, photo: Dict[str, Any]) -> Dict[str, Any]:
        """Pexels 이미지 응답 파싱"""
        return {
            "provider": "pexels",
            "asset_type": "IMAGE",
            "source_url": photo["src"]["original"],
            "thumbnail_url": photo["src"]["medium"],
            "title": photo.get("alt", ""),
            "license": "Pexels License",
            "meta": {
                "photographer": photo.get("photographer"),
                "photographer_url": photo.get("photographer_url"),
                "pexels_id": photo.get("id"),
                "width": photo.get("width"),
                "height": photo.get("height")
            }
        }

    def _parse_video(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """Pexels 영상 응답 파싱"""
        # 가장 적합한 영상 파일 선택 (HD 우선)
        video_files = video.get("video_files", [])
        best_file = None

        for vf in video_files:
            if vf.get("quality") == "hd":
                best_file = vf
                break

        if not best_file and video_files:
            best_file = video_files[0]

        return {
            "provider": "pexels",
            "asset_type": "VIDEO",
            "source_url": best_file.get("link", "") if best_file else "",
            "thumbnail_url": video.get("image", ""),
            "title": "",
            "license": "Pexels License",
            "meta": {
                "duration": video.get("duration"),
                "pexels_id": video.get("id"),
                "width": best_file.get("width") if best_file else None,
                "height": best_file.get("height") if best_file else None,
                "user": video.get("user", {}).get("name")
            }
        }
