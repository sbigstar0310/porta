from typing import Optional
from repo.report_repo import ReportRepo
from data.schemas import ReportOut, ReportCreate, ReportPatch
import asyncio
import logging

logger = logging.getLogger(__name__)


class ReportUsecase:
    def __init__(self, report_repo: ReportRepo):
        self.report_repo = report_repo

    async def create_report(self, user_id: int, report_md: str, language: str = "ko") -> ReportOut:
        """
        보고서 생성

        Args:
            user_id: 사용자 ID
            report_md: 마크다운 형식의 보고서 내용
            language: 언어 코드 (기본: ko)

        Returns:
            ReportOut: 생성된 보고서 정보
        """
        try:
            schema = ReportCreate(user_id=user_id, report_md=report_md, language=language)
            result = await self.report_repo.create(schema)
            logger.info(f"보고서 생성 완료: user_id={user_id}, report_id={result.id}")
            return result
        except Exception as e:
            logger.error(f"보고서 생성 실패: user_id={user_id}, error={e}")
            raise e

    def create_report_sync(self, user_id: int, report_md: str, language: str = "ko") -> ReportOut:
        """
        `create_report`의 동기 버전
        """
        try:
            schema = ReportCreate(user_id=user_id, report_md=report_md, language=language)

            # 새로운 이벤트 루프 생성하여 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.report_repo.create(schema))
                return result
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"보고서 생성 실패: user_id={user_id}, error={e}")
            raise e

    async def get_report(self, report_id: int, user_id: int) -> Optional[ReportOut]:
        """
        보고서 조회 (권한 확인 포함)

        Args:
            report_id: 보고서 ID
            user_id: 요청한 사용자 ID (권한 확인용)

        Returns:
            Optional[ReportOut]: 보고서 정보
        """
        try:
            report = await self.report_repo.get_by_id(report_id)

            if not report:
                logger.warning(f"보고서를 찾을 수 없습니다: report_id={report_id}")
                return None

            # 권한 확인: 본인의 보고서만 조회 가능
            if report.user_id != user_id:
                logger.warning(
                    f"보고서 접근 권한 없음: report_id={report_id}, user_id={user_id}, owner_id={report.user_id}"
                )
                return None

            return report
        except Exception as e:
            logger.error(f"보고서 조회 실패: report_id={report_id}, error={e}")
            raise e

    async def get_user_reports(
        self, user_id: int, page: int = 1, page_size: int = 20, order_by: str = "created_at", desc: bool = True
    ) -> dict:
        """
        사용자별 보고서 목록 조회 (페이지네이션)

        Args:
            user_id: 사용자 ID
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지 크기 (기본 20)
            order_by: 정렬 기준 필드 (기본 created_at)
            desc: 내림차순 여부 (기본 True)

        Returns:
            dict: 보고서 목록과 페이지네이션 정보
        """
        try:
            # 페이지 계산
            offset = (page - 1) * page_size

            # 보고서 목록 조회
            reports = await self.report_repo.get_by_user_id(
                user_id=user_id, limit=page_size, offset=offset, order_by=order_by, desc=desc
            )

            # 총 개수 조회
            total_count = await self.report_repo.count_by_user_id(user_id)
            total_pages = (total_count + page_size - 1) // page_size

            result = {
                "reports": reports,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1,
                },
            }

            logger.info(f"사용자 보고서 목록 조회 완료: user_id={user_id}, page={page}, count={len(reports)}")
            return result
        except Exception as e:
            logger.error(f"사용자 보고서 목록 조회 실패: user_id={user_id}, error={e}")
            raise e

    async def get_latest_report(self, user_id: int) -> Optional[ReportOut]:
        """
        사용자의 최신 보고서 조회

        Args:
            user_id: 사용자 ID

        Returns:
            Optional[ReportOut]: 최신 보고서 정보
        """
        try:
            result = await self.report_repo.get_latest_by_user_id(user_id)
            if result:
                logger.info(f"최신 보고서 조회 완료: user_id={user_id}, report_id={result.id}")
            else:
                logger.info(f"최신 보고서 없음: user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"최신 보고서 조회 실패: user_id={user_id}, error={e}")
            raise e

    async def update_report(self, report_id: int, user_id: int, schema: ReportPatch) -> Optional[ReportOut]:
        """
        보고서 수정 (권한 확인 포함)

        Args:
            report_id: 보고서 ID
            user_id: 요청한 사용자 ID (권한 확인용)
            schema: 수정할 보고서 정보

        Returns:
            Optional[ReportOut]: 수정된 보고서 정보
        """
        try:
            # 기존 보고서 조회 및 권한 확인
            existing_report = await self.get_report(report_id, user_id)
            if not existing_report:
                logger.warning(f"수정할 보고서가 없거나 권한이 없습니다: report_id={report_id}, user_id={user_id}")
                return None

            # 보고서 수정
            result = await self.report_repo.update(report_id, schema)
            if result:
                logger.info(f"보고서 수정 완료: report_id={report_id}, user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"보고서 수정 실패: report_id={report_id}, user_id={user_id}, error={e}")
            raise e

    async def delete_report(self, report_id: int, user_id: int) -> bool:
        """
        보고서 삭제 (권한 확인 포함)

        Args:
            report_id: 보고서 ID
            user_id: 요청한 사용자 ID (권한 확인용)

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 기존 보고서 조회 및 권한 확인
            existing_report = await self.get_report(report_id, user_id)
            if not existing_report:
                logger.warning(f"삭제할 보고서가 없거나 권한이 없습니다: report_id={report_id}, user_id={user_id}")
                return False

            # 보고서 삭제
            result = await self.report_repo.delete_by_id(report_id)
            if result:
                logger.info(f"보고서 삭제 완료: report_id={report_id}, user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"보고서 삭제 실패: report_id={report_id}, user_id={user_id}, error={e}")
            raise e
