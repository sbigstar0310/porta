from worker.constants import Constants
from worker.utils import to_crontab
from worker.worker import celery_app
from clients import get_email_client
from usecase import get_user_usecase, get_portfolio_usecase, get_report_usecase, get_schedule_usecase, ScheduleUsecase
from dotenv import load_dotenv
from celery.utils.log import get_task_logger
from celery import Task
import asyncio
import os
from typing import Any
import time
from redbeat import RedBeatSchedulerEntry

logger = get_task_logger(__name__)

# 모듈 레벨 캐시
_dependencies_cache = None
_is_initialized = False


async def _initialize_dependencies_once() -> dict[str, Any]:
    """
    의존성을 한 번만 초기화하여 캐시하는 함수

    Returns:
        dict[str, Any]: 모든 의존성이 포함된 딕셔너리
    """
    global _dependencies_cache, _is_initialized

    if _is_initialized and _dependencies_cache:
        logger.debug("캐시된 의존성 반환")
        return _dependencies_cache

    logger.info("의존성 초기화 시작...")

    try:
        # 환경변수 로드 (한 번만)
        if not os.getenv("OPENAI_API_KEY"):
            load_dotenv()
            logger.debug("환경변수 로드 완료")

        # DB 초기화 (싱글톤이므로 안전)
        from data.db import Database

        await Database.initialize()
        logger.debug("데이터베이스 초기화 완료")

        # 모든 의존성 생성
        _dependencies_cache = {
            "email_client": get_email_client(),
            "portfolio_usecase": get_portfolio_usecase(),
            "report_usecase": get_report_usecase(),
            "user_usecase": get_user_usecase(),
            "schedule_usecase": get_schedule_usecase(),
        }

        _is_initialized = True
        logger.info(f"의존성 초기화 완료: {list(_dependencies_cache.keys())}")
        return _dependencies_cache

    except Exception as e:
        logger.error(f"의존성 초기화 실패: {e}")
        _is_initialized = False
        _dependencies_cache = None
        raise Exception(f"Critical dependency initialization failed: {e}") from e


async def _initialize_dependencies(
    return_email_client: bool = True,
    return_portfolio_usecase: bool = True,
    return_report_usecase: bool = True,
    return_user_usecase: bool = True,
    return_schedule_usecase: bool = True,
) -> dict[str, Any]:
    """
    필요한 의존성만 선택적으로 반환하는 함수

    Args:
        return_email_client: bool = True,
        return_portfolio_usecase: bool = True,
        return_report_usecase: bool = True,
        return_user_usecase: bool = True,
        return_schedule_usecase: bool = True,

    Returns:
        dict[str, Any]: 선택된 의존성들

    Raises:
        Exception: 의존성 초기화 실패 시
    """
    try:
        # 전체 의존성 캐시에서 가져오기
        all_deps = await _initialize_dependencies_once()

        # 필요한 것만 필터링
        dependencies = {}
        if return_email_client and "email_client" in all_deps:
            dependencies["email_client"] = all_deps["email_client"]
        if return_portfolio_usecase and "portfolio_usecase" in all_deps:
            dependencies["portfolio_usecase"] = all_deps["portfolio_usecase"]
        if return_report_usecase and "report_usecase" in all_deps:
            dependencies["report_usecase"] = all_deps["report_usecase"]
        if return_user_usecase and "user_usecase" in all_deps:
            dependencies["user_usecase"] = all_deps["user_usecase"]
        if return_schedule_usecase and "schedule_usecase" in all_deps:
            dependencies["schedule_usecase"] = all_deps["schedule_usecase"]

        logger.debug(f"의존성 필터링 완료: {list(dependencies.keys())}")
        return dependencies

    except Exception as e:
        logger.error(f"의존성 필터링 실패: {e}")
        raise


async def _run_agent_async(
    task_instance: Task,
    current_user_id: int,
):
    """
    Langraph agent 실행

    Args:
        current_user_id: 사용자 ID
    """
    from graph.app import run_graph
    from worker.utils import update_progress

    # Initialize dependencies
    try:
        update_progress(task_instance, 0.0, "실행 준비 중")
        dependencies = await _initialize_dependencies()
        update_progress(task_instance, 5.0, "실행 준비 완료")
    except Exception as e:
        logger.error(f"Error initializing clients and usecases: {e}")
        raise

    try:
        logger.info(f"Starting agent task for user {current_user_id}")

        # 1. 포트폴리오 조회
        update_progress(task_instance, 10.0, "포트폴리오 조회 중...")
        portfolio = await dependencies["portfolio_usecase"].get_current_portfolio(user_id=current_user_id)
        if not portfolio:
            raise Exception("Portfolio not found")

        # 2. 유저 정보
        update_progress(task_instance, 12.0, "사용자 정보 조회 중...")
        user = dependencies["user_usecase"].get_user_profile(user_id=current_user_id)
        if not user:
            raise Exception("User not found")

        # 3. Langraph 실행
        update_progress(task_instance, 15.0, "에이전트 파이프라인 실행 중...")
        result = run_graph(portfolio=portfolio, user_id=current_user_id, language=user.language)
        logger.info(f"Agent run result: {result}")
        update_progress(task_instance, 90.0, "에이전트 실행 완료")

        # 4. 보고서 저장
        update_progress(task_instance, 95.0, "보고서 저장 중...")
        report_md = result.get("report_md", "NO REPORT")
        report = await dependencies["report_usecase"].create_report(
            user_id=current_user_id,
            report_md=report_md,
            language="ko",
        )
        logger.info(f"Agent report saved: {report}")

        # 5. 이메일 전송
        update_progress(task_instance, 98.0, "이메일 전송 중...")
        response = dependencies["email_client"].send_markdown_email_with_pdf(
            to=user.email,
            subject="[Porta] 에이전트 보고서 결과",
            markdown_content=report_md,
        )
        logger.info(f"Agent email sent: {response}")
        update_progress(task_instance, 100.0, "완료")

        return {"status": "success", "result": result}

    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        raise


def _run_agent_with_check(current_user_id: int) -> bool:
    """
    Check if agent is already running

    Args:
        current_user_id: 사용자 ID

    Returns:
        bool: (true: 실행 중, false: 실행 중이 아님)
    """
    try:
        # Check if agent is already running
        from usecase import get_task_usecase

        task_usecase = get_task_usecase()
        if task_usecase.check_existing_running_task(current_user_id)["is_running"]:
            return True
    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        raise

    return False


@celery_app.task(bind=True)
def run_agent_task(self: Task, current_user_id: int):
    try:
        # Check if agent is already running
        if _run_agent_with_check(current_user_id):
            logger.info(f"Agent is already running for user {current_user_id}")
            return

        # Run agent
        return asyncio.run(_run_agent_async(self, current_user_id))
    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        raise


@celery_app.task(bind=True)
def run_scheduled_agent_task(self: Task, current_user_id: int):
    try:
        # Check if agent is already running
        if _run_agent_with_check(current_user_id):
            logger.info(f"Agent is already running for user {current_user_id}")
            return

        # Run agent
        return asyncio.run(_run_agent_async(self, current_user_id))
    except Exception as e:
        logger.error(f"Agent task failed: {e}")
        raise


async def _sync_all_schedules_async():
    sync_start_time = time.monotonic()

    try:
        # RedBeat을 사용하여 현재 Redis에 저장된 모든 스케줄 가져오기
        live_keys = set()

        # 의존성 초기화 (schedule_usecase만 필요)
        dependencies = await _initialize_dependencies(
            return_email_client=False,
            return_portfolio_usecase=False,
            return_report_usecase=False,
            return_user_usecase=False,
            return_schedule_usecase=True,
        )

        schedule_usecase: ScheduleUsecase | None = dependencies.get("schedule_usecase", None)
        if not schedule_usecase:
            raise Exception("ScheduleUsecase 초기화 실패 - 의존성을 확인해주세요")

        # DB에서 모든 활성화된 스케줄 조회
        try:
            schedules = await schedule_usecase.get_all_enabled_schedules()
        except Exception as e:
            logger.error(f"DB 스케줄 조회 실패: {e}")
            raise Exception(f"Failed to fetch schedules from DB: {e}") from e

        # 각 스케줄을 RedBeat에 upsert
        upserted_count = 0
        for schedule in schedules:
            try:
                # ScheduleOut 객체에서 필요한 정보 추출
                user_id = schedule.user_id
                hour = schedule.hour
                minute = schedule.minute
                timezone = schedule.timezone

                # 스케줄 키 생성
                key = f"{Constants.USER_SCHEDULE_KEY_PREFIX}{user_id}"
                live_keys.add(key)

                # Celery crontab 생성
                try:
                    crontab_schedule = to_crontab({"hour": hour, "minute": minute, "timezone": timezone})
                except Exception as e:
                    logger.error(f"crontab 생성 실패 - 스킵: user_id={user_id}, tz={timezone}, error={e}")
                    continue

                # RedBeat Entry 생성 또는 업데이트
                try:
                    # 기존 entry가 있으면 가져오기
                    entry = RedBeatSchedulerEntry.from_key(key, app=celery_app)
                    # 스케줄 업데이트
                    entry.schedule = crontab_schedule
                except KeyError:
                    # 새로운 entry 생성
                    entry = RedBeatSchedulerEntry(
                        key,
                        Constants.SCHEDULED_AGENT_TASK,
                        crontab_schedule,
                        args=(user_id,),
                        kwargs={},
                        options={"queue": "agent"},
                        app=celery_app,
                    )
                entry.save()
                upserted_count += 1

            except Exception as e:
                logger.error(f"스케줄 처리 실패 - 스킵: schedule_id={schedule.id}, error={e}")
                continue

        # Prune: DB에 없는 사용자 스케줄 제거 (Redis에서)
        removed_count = 0
        # RedBeat에서 모든 스케줄 키 가져오기
        try:
            from redbeat.schedulers import get_redis

            redis_client = get_redis(celery_app)
            redbeat_key_prefix = "redbeat:"
            all_keys = redis_client.keys(f"{redbeat_key_prefix}*")

            for redis_key in all_keys:
                # redbeat: 접두사 제거
                key = redis_key.decode() if isinstance(redis_key, bytes) else redis_key
                key_without_prefix = key.replace(redbeat_key_prefix, "")

                # 사용자 스케줄이고 live_keys에 없으면 제거
                if (
                    key_without_prefix.startswith(Constants.USER_SCHEDULE_KEY_PREFIX)
                    and key_without_prefix not in live_keys
                ):
                    try:
                        entry = RedBeatSchedulerEntry.from_key(key, app=celery_app)
                        entry.delete()
                        removed_count += 1
                    except Exception as e:
                        logger.warning(f"스케줄 제거 실패: {key}, error={e}")
        except Exception as e:
            logger.warning(f"스케줄 정리 중 오류 발생: {e}")

        # 실행 시간 계산
        sync_duration = time.monotonic() - sync_start_time

        result = {
            "status": "success",
            "active_schedules": len(live_keys),
            "removed_schedules": removed_count,
            "total_schedules": len(live_keys),
            "sync_duration_seconds": round(sync_duration, 3),
            "upserted_count": upserted_count,
        }

        logger.info(
            f"스케줄 동기화 완료: "
            f"활성 {result['active_schedules']}개, "
            f"제거 {result['removed_schedules']}개, "
            f"전체 {result['total_schedules']}개 "
            f"(소요시간: {result['sync_duration_seconds']}초)"
        )

        return result

    except Exception as e:
        sync_duration = time.monotonic() - sync_start_time
        logger.error(f"스케줄 동기화 실패 (소요시간: {sync_duration:.3f}초): {e}")

        # 상세 오류 정보
        import traceback

        logger.error(f"상세 오류 정보:\n{traceback.format_exc()}")

        raise Exception(f"Schedule synchronization failed: {e}") from e


@celery_app.task(bind=True)
def sync_all_schedules(self):
    """
    DB에서 모든 활성화된 스케줄을 조회하여 Celery Beat 메모리 스케줄에 동기화
    - 새로운 스케줄은 추가 (upsert)
    - DB에 없는 스케줄은 제거 (prune)

    Returns:
        dict: 동기화 결과

    Raises:
        Exception: 동기화 실패 시
    """
    task_start_time = time.monotonic()

    try:
        result = asyncio.run(_sync_all_schedules_async())
        task_duration = time.monotonic() - task_start_time
        return result

    except Exception as e:
        task_duration = time.monotonic() - task_start_time
        logger.error(f"스케줄 동기화 태스크 실패 - 소요시간: {task_duration:.3f}초, error: {e}")

        # Celery에서 재시도 가능하도록 예외 재발생
        raise Exception(f"Schedule sync task failed: {e}") from e
