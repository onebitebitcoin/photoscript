import re
from typing import List
from app.utils.logger import logger


def split_into_sentences(text: str) -> List[str]:
    """텍스트를 문장 단위로 분할"""
    # 한국어/영어 문장 분리 패턴
    # 마침표, 물음표, 느낌표 뒤에 공백이나 줄바꿈이 오는 경우
    pattern = r'(?<=[.!?。？！])\s+'
    sentences = re.split(pattern, text)
    return [s.strip() for s in sentences if s.strip()]


def split_script(script_raw: str, max_length: int = 500) -> List[str]:
    """
    스크립트를 블록으로 분할

    분할 정책:
    1. 빈 줄(공백 라인) 기준으로 문단 분할
    2. 문단이 max_length 초과 시 문장 단위로 추가 분할

    Args:
        script_raw: 원본 스크립트 텍스트
        max_length: 블록 최대 길이 (기본 500자)

    Returns:
        분할된 블록 텍스트 리스트
    """
    logger.info(f"스크립트 분할 시작: {len(script_raw)}자")

    # 빈 줄로 문단 분할
    paragraphs = re.split(r'\n\s*\n', script_raw.strip())
    blocks = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 문단이 최대 길이 이하면 그대로 블록으로
        if len(para) <= max_length:
            blocks.append(para)
            logger.debug(f"블록 추가 (문단): {len(para)}자")
        else:
            # 문단이 너무 길면 문장 단위로 분할
            sentences = split_into_sentences(para)
            current_block = ""

            for sent in sentences:
                # 현재 블록에 문장을 추가해도 최대 길이 이하인 경우
                if len(current_block) + len(sent) + 1 <= max_length:
                    if current_block:
                        current_block += " " + sent
                    else:
                        current_block = sent
                else:
                    # 현재 블록 저장하고 새 블록 시작
                    if current_block:
                        blocks.append(current_block.strip())
                        logger.debug(f"블록 추가 (문장분할): {len(current_block)}자")
                    current_block = sent

            # 남은 텍스트 저장
            if current_block:
                blocks.append(current_block.strip())
                logger.debug(f"블록 추가 (마지막): {len(current_block)}자")

    logger.info(f"스크립트 분할 완료: {len(blocks)}개 블록 생성")
    return blocks
