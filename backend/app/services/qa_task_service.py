"""
QA Task 비동기 처리 서비스
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.qa_task import QATask
from app.models.project import Project
from app.services.qa_service import validate_and_correct_script
from app.services.qa_version_service import QAVersionService
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class QATaskService:
    """QA 작업 비동기 처리"""

    def __init__(self):
        self.qa_version_service = QAVersionService()

    def create_task(
        self,
        db: Session,
        project_id: str,
        additional_prompt: Optional[str] = None
    ) -> QATask:
        """QA 작업 생성"""
        task = QATask(
            project_id=project_id,
            status="pending",
            progress=0,
            additional_prompt=additional_prompt
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        logger.info(f"QA 작업 생성: task_id={task.id}, project_id={project_id}")
        return task

    def get_task(self, db: Session, task_id: str) -> Optional[QATask]:
        """작업 조회"""
        return db.query(QATask).filter(QATask.id == task_id).first()

    async def execute_qa_task(self, task_id: str):
        """백그라운드에서 QA 검증 실행"""
        db = SessionLocal()
        try:
            task = db.query(QATask).filter(QATask.id == task_id).first()
            if not task:
                logger.error(f"작업을 찾을 수 없음: task_id={task_id}")
                return

            # 상태 업데이트: running
            task.status = "running"
            task.progress = 10
            db.commit()
            logger.info(f"QA 작업 시작: task_id={task_id}")

            # 프로젝트 및 블록 조회
            project = db.query(Project).filter(Project.id == task.project_id).first()
            if not project:
                raise ValueError(f"프로젝트를 찾을 수 없음: {task.project_id}")

            # 블록에서 전체 스크립트 구성
            blocks = sorted(project.blocks, key=lambda b: b.order)
            full_script = "\n\n".join([block.text for block in blocks if block.text])

            if not full_script:
                raise ValueError("블록에 텍스트가 없습니다")

            # 진행률 업데이트
            task.progress = 30
            db.commit()

            # 사용자 설정 조회 (커스텀 가이드라인)
            custom_guideline = project.user.qa_custom_guideline if project.user else None

            # 진행률 업데이트
            task.progress = 50
            db.commit()

            # QA 검증 실행
            logger.info(f"QA 검증 시작: task_id={task_id}, script_length={len(full_script)}")
            qa_result = await validate_and_correct_script(
                full_script=full_script,
                additional_prompt=task.additional_prompt,
                custom_guideline=custom_guideline
            )

            # 진행률 업데이트
            task.progress = 80
            db.commit()

            # 결과를 JSON으로 직렬화
            result_json = qa_result.model_dump_json()

            # 버전 저장
            try:
                self.qa_version_service.create_version(
                    db=db,
                    project_id=task.project_id,
                    corrected_script=qa_result.corrected_script,
                    model=qa_result.model,
                    input_tokens=qa_result.input_tokens,
                    output_tokens=qa_result.output_tokens
                )
                logger.info(f"QA 버전 저장 완료: task_id={task_id}")
            except Exception as e:
                logger.warning(f"QA 버전 저장 실패 (경고만): {e}")

            # 작업 완료
            task.status = "completed"
            task.progress = 100
            task.result_json = result_json
            task.completed_at = datetime.utcnow()
            db.commit()

            logger.info(f"QA 작업 완료: task_id={task_id}")

        except Exception as e:
            logger.error(f"QA 작업 실패: task_id={task_id}, error={str(e)}", exc_info=True)
            try:
                task = db.query(QATask).filter(QATask.id == task_id).first()
                if task:
                    task.status = "failed"
                    task.error_message = str(e)
                    task.completed_at = datetime.utcnow()
                    db.commit()
            except Exception as commit_error:
                logger.error(f"작업 실패 상태 업데이트 실패: {commit_error}")
        finally:
            db.close()

    def start_background_task(self, task_id: str):
        """백그라운드에서 작업 시작"""
        asyncio.create_task(self.execute_qa_task(task_id))
        logger.info(f"백그라운드 작업 시작: task_id={task_id}")


qa_task_service = QATaskService()
