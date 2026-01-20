"""
유튜브 스크립트 QA 검증 서비스

LLM API를 통해:
1. 스크립트 진단 (문제점 3개 + 장점 2개)
2. 5블록 구조 점검 (Hook/맥락/Promise/Body/Wrap-up)
3. 보정 스크립트 생성
4. 변경 로그 생성
"""

import json
import re
from typing import Dict, Any
from datetime import datetime
from openai import AsyncOpenAI
from app.config import get_settings
from app.utils.logger import logger
from app.schemas.project import (
    QAScriptResponse,
    DiagnosisSummary,
    StructureCheck,
    ChangeLogItem
)

settings = get_settings()


class QAServiceError(Exception):
    """QA 서비스 실패 예외"""
    pass


# 기본 유튜브 스크립트 가이드라인 (fallback)
DEFAULT_QA_GUIDELINE = """
## 유튜브 스크립트 작성 가이드라인

### 필수 규칙 (CRITICAL)
1. **입니다/합니다체 강제**: 모든 문장은 "~입니다", "~합니다"로 끝나야 함
2. **지시어 금지**: "이것", "그것", "자 이제", "여러분" 등 지시어 사용 금지
3. **AI 진행 멘트 금지**: "다음으로 넘어가서", "이제 설명하겠습니다" 등 금지
4. **다음 영상 예고 금지**: "다음 영상에서는..." 등 금지
5. **자연스러운 리듬**: 문장이 너무 끊기지 않고 자연스럽게 흐르도록

### 5블록 구조 (필수)
1. **Hook**: 시청자 관심 유도 (1~2문장)
2. **맥락**: 주제 배경 설명 (2~3문장)
3. **Promise + Outline**: 영상에서 다룰 내용 예고 (2~3문장)
4. **Body**: 핵심 내용 전달 (메인 콘텐츠)
5. **Wrap-up**: 마무리 및 요약 (1~2문장)

### 보정 원칙 (CRITICAL)
- **원본 내용과 길이 완전 유지**: 절대로 내용을 줄이거나 요약하지 말 것
- **형식만 수정**: 문체(입니다/합니다체), 지시어 제거 등 형식과 표현만 수정
- **정보 보존**: 원본의 모든 정보, 예시, 설명을 그대로 유지

### 진단 기준
- 문제점 3개: 가이드라인 위반 사항
- 장점 2개: 잘 작성된 부분
"""


async def validate_and_correct_script(
    full_script: str,
    additional_prompt: str = None,
    custom_guideline: str = None
) -> QAScriptResponse:
    """
    유튜브 스크립트를 QA 검증하고 보정

    Args:
        full_script: 전체 스크립트 텍스트
        additional_prompt: 추가 프롬프트 (선택사항)
        custom_guideline: 커스텀 QA 가이드라인 (없으면 기본값 사용)

    Returns:
        QAScriptResponse: 진단, 구조 점검, 보정 스크립트, 변경 로그

    Raises:
        QAServiceError: QA 검증 실패 시
    """
    logger.info(f"QA 검증 시작: {len(full_script)}자, 추가 프롬프트: {bool(additional_prompt)}, 커스텀 가이드라인: {bool(custom_guideline)}")

    if not settings.openai_api_key:
        logger.error("OpenAI API 키가 설정되지 않음")
        raise QAServiceError("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

    if not full_script or not full_script.strip():
        logger.error("빈 스크립트")
        raise QAServiceError("스크립트가 비어있습니다.")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # 커스텀 가이드라인이 있으면 사용, 없으면 기본 가이드라인 사용
    qa_guideline = custom_guideline if custom_guideline else DEFAULT_QA_GUIDELINE

    system_prompt = f"""당신은 유튜브 스크립트 QA 전문가입니다.
스크립트를 분석하여 가이드라인 준수 여부를 점검하고, 보정된 스크립트를 제공합니다.

{qa_guideline}

## 출력 형식 (반드시 JSON으로만 응답)
{{
  "diagnosis": {{
    "problems": ["문제1", "문제2", "문제3"],
    "strengths": ["장점1", "장점2"]
  }},
  "structure_check": {{
    "has_hook": true/false,
    "has_context": true/false,
    "has_promise_outline": true/false,
    "has_body": true/false,
    "has_wrapup": true/false,
    "overall_pass": true/false,
    "comments": "구조 관련 코멘트"
  }},
  "corrected_script": "보정된 전체 스크립트 텍스트",
  "change_logs": [
    {{"block_index": 0, "change_type": "수정", "description": "입니다체로 변경"}},
    {{"block_index": 1, "change_type": "삭제", "description": "지시어 제거"}}
  ]
}}

중요 (CRITICAL):
- 반드시 위 JSON 형식으로만 응답하세요.
- corrected_script는 **원본 스크립트의 모든 내용과 길이를 그대로 유지**하면서 가이드라인 위반 사항만 수정한 것입니다.
- **절대로 내용을 줄이거나 요약하지 마세요.** 원본의 모든 정보와 분량을 그대로 유지해야 합니다.
- 단어 선택, 문체(입니다/합니다체), 지시어 제거 등 형식과 표현만 가이드라인에 맞게 수정하세요.
- 원본 스크립트의 문단 구조와 흐름을 그대로 유지하세요.
- change_logs는 원본 대비 주요 변경사항을 블록별로 기록합니다.
"""

    # 추가 프롬프트가 있으면 시스템 프롬프트에 추가
    if additional_prompt:
        system_prompt += f"\n\n## 추가 요구사항\n{additional_prompt}\n"

    # 시스템 프롬프트와 사용자 프롬프트를 하나로 합침
    combined_prompt = f"""{system_prompt}

다음 유튜브 스크립트를 검증하고 보정해주세요.

**매우 중요: 아래 스크립트의 모든 내용과 길이를 그대로 유지하면서, 가이드라인 위반 사항(문체, 지시어 등)만 수정하세요. 절대로 요약하거나 줄이지 마세요.**

원본 스크립트:
---
{full_script}
---
"""

    try:
        logger.debug("OpenAI API 호출 시작")

        response = await client.responses.create(
            model="gpt-5-mini",
            input=combined_prompt,
            max_output_tokens=128000  # 최대 출력 토큰 (한국어 약 50,000단어 이상)
        )

        content = response.output_text.strip()
        logger.debug(f"OpenAI 응답: {content[:500]}...")

        # 토큰 사용량 추출
        input_tokens = response.usage.input_tokens if hasattr(response, 'usage') else None
        output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else None
        logger.info(f"토큰 사용량 - 입력: {input_tokens}, 출력: {output_tokens}")

        # JSON 추출 (마크다운 코드 블록 제거)
        json_content = _extract_json(content)

        # JSON 파싱
        data = json.loads(json_content)

        # Pydantic 모델로 변환
        qa_result = QAScriptResponse(
            diagnosis=DiagnosisSummary(**data["diagnosis"]),
            structure_check=StructureCheck(**data["structure_check"]),
            corrected_script=data["corrected_script"],
            change_logs=[ChangeLogItem(**log) for log in data.get("change_logs", [])],
            model="gpt-5-mini",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            created_at=datetime.now()
        )

        logger.info("QA 검증 완료")
        return qa_result

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        logger.error(f"응답 내용: {content if 'content' in locals() else 'N/A'}")
        raise QAServiceError(f"LLM 응답을 파싱할 수 없습니다: {e}")
    except KeyError as e:
        logger.error(f"필수 필드 누락: {e}")
        raise QAServiceError(f"LLM 응답에 필수 필드가 없습니다: {e}")
    except Exception as e:
        logger.error(f"QA 검증 실패: {e}")
        raise QAServiceError(f"QA 검증 실패: {e}")


def _extract_json(text: str) -> str:
    """
    텍스트에서 JSON 추출 (마크다운 코드 블록 제거)

    Args:
        text: LLM 응답 텍스트

    Returns:
        순수 JSON 문자열
    """
    # 마크다운 코드 블록 제거 (```json ... ```)
    json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(json_pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()

    # 코드 블록이 없으면 원본 반환
    return text.strip()
