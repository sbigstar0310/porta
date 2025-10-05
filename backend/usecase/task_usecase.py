from worker.worker import celery_app
from data.schemas import TaskProgressOut
import logging

logger = logging.getLogger(__name__)


class TaskUsecase:
    def __init__(self):
        pass

    def check_existing_running_task(self, current_user_id: int) -> dict:
        """
        해당 유저의 실행 중인 태스크가 있는지 확인합니다.

        Args:
            current_user_id: 현재 사용자 ID

        Returns:
            dict: 실행 중인 태스크 정보

        Examples:
            >>> task_usecase.check_existing_running_task(1)
            {
                "is_running": True,
                "task_id": "1234567890",
            }

            >>> task_usecase.check_existing_running_task(2)
            {
                "is_running": False,
                "task_id": None,
            }
        """
        # 현재 활성 태스크 검색
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        # 활성 태스크가 없으면 False 반환
        if not active_tasks:
            return {
                "is_running": False,
                "task_id": None,
            }

        # 해당 유저의 실행 중인 태스크 확인
        for _, tasks in active_tasks.items():
            if not tasks:
                continue

            # 해당 유저의 실행 중인 태스크 확인
            for task in tasks:
                if task.get("name") == "worker.tasks.run_agent_task":
                    # Get task args
                    args = task.get("args", [])
                    if args and len(args) > 0 and args[0] == current_user_id:
                        logger.info(f"User {current_user_id} already has running task: {task['id']}")
                        return {
                            "is_running": True,
                            "task_id": task["id"],
                        }

        return {
            "is_running": False,
            "task_id": None,
        }

    def check_existing_running_task_excluding(self, current_user_id: int, current_task_id: str) -> dict:
        """
        해당 유저의 실행 중인 태스크가 있는지 확인합니다 (현재 태스크 제외).

        Args:
            current_user_id: 현재 사용자 ID
            current_task_id: 현재 태스크 ID (제외할 태스크)

        Returns:
            dict: 실행 중인 태스크 정보
        """
        # 현재 활성 태스크 검색
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        # 활성 태스크가 없으면 False 반환
        if not active_tasks:
            return {
                "is_running": False,
                "task_id": None,
            }

        # 해당 유저의 실행 중인 태스크 확인 (현재 태스크 제외)
        for _, tasks in active_tasks.items():
            if not tasks:
                continue

            # 해당 유저의 실행 중인 태스크 확인
            for task in tasks:
                if task.get("name") == "worker.tasks.run_agent_task":
                    task_id = task.get("id")

                    # 현재 태스크는 제외
                    if task_id == current_task_id:
                        logger.debug(f"Skipping current task {current_task_id} for user {current_user_id}")
                        continue

                    # Get task args
                    args = task.get("args", [])
                    if args and len(args) > 0 and args[0] == current_user_id:
                        logger.info(
                            f"User {current_user_id} already has running task: {task_id} \
                                (excluding current: {current_task_id})"
                        )
                        return {
                            "is_running": True,
                            "task_id": task_id,
                        }

        return {
            "is_running": False,
            "task_id": None,
        }

    def cancel_task(self, task_id: str) -> bool:
        """
        태스크 취소

        Args:
            task_id: 태스크 ID

        Returns:
            bool: 취소 성공 여부
        """
        try:
            celery_app.control.revoke(task_id, terminate=True)
        except Exception as e:
            logger.error(f"태스크 취소 실패 (task_id: {task_id}): {e}")
            return False

        return True

    def get_task_progress(self, task_id: str) -> TaskProgressOut:
        """
        태스크 진행 상황 조회

        Args:
            task_id: 태스크 ID

        Returns:
            TaskProgressOut: 태스크 진행 상황
        """
        # Celery 태스크 상태 조회
        task_result = celery_app.AsyncResult(task_id)

        # 기본 응답 구성
        response = TaskProgressOut(
            task_id=task_id,
            status=task_result.status,
            percent=0.0,
        )

        if task_result.status == "PENDING":
            response.percent = 0.0
            response.message = "태스크가 대기 중입니다."

        elif task_result.status == "STARTED":
            response.percent = 0.0
            response.message = "태스크가 시작되었습니다."

        elif task_result.status == "PROGRESS":
            # 진행 중인 경우 메타데이터에서 상세 정보 추출
            if task_result.info:
                response.percent = task_result.info.get("percent", 0.0)
                response.message = task_result.info.get("message", "태스크가 진행 중입니다.")
            else:
                response.message = "태스크가 진행 중입니다."

        elif task_result.status == "SUCCESS":
            response.percent = 100.0
            response.message = "태스크가 성공적으로 완료되었습니다."
            response.result = task_result.result

        elif task_result.status == "FAILURE":
            response.percent = 0.0
            response.message = "태스크 실행 중 오류가 발생했습니다."
            response.error = str(task_result.info) if task_result.info else "알 수 없는 오류"

        elif task_result.status == "REVOKED":
            response.percent = 0.0
            response.message = "태스크가 취소되었습니다."

        else:
            response.message = f"알 수 없는 태스크 상태: {task_result.status}"

        return response
