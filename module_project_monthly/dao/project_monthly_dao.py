from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_project_monthly.entity.do.project_monthly_do import OaProjectMonthly
from module_project_monthly.entity.vo.project_monthly_vo import ProjectMonthlyPageQueryModel
from utils.common_util import CamelCaseUtil
from utils.time_format_util import timestamp_to_datetime


class ProjectMonthlyDao:
    """月度项目台账数据库操作层"""

    @staticmethod
    def _build_conditions(query_object: ProjectMonthlyPageQueryModel) -> list[Any]:
        conditions: list[Any] = [OaProjectMonthly.delete_time == 0]
        if query_object.stat_month:
            conditions.append(OaProjectMonthly.stat_month == query_object.stat_month)
        if query_object.customer_name:
            conditions.append(OaProjectMonthly.customer_name.like(f'%{query_object.customer_name}%'))
        if query_object.project_name:
            conditions.append(OaProjectMonthly.project_name.like(f'%{query_object.project_name}%'))
        if query_object.contract_signed is not None:
            conditions.append(OaProjectMonthly.contract_signed == query_object.contract_signed)
        if query_object.project_closed is not None:
            conditions.append(OaProjectMonthly.project_closed == query_object.project_closed)
        if query_object.keywords:
            keyword = f'%{query_object.keywords}%'
            conditions.append(
                OaProjectMonthly.customer_name.like(keyword) | OaProjectMonthly.project_name.like(keyword)
            )
        return conditions

    @classmethod
    def _to_dict(cls, row: OaProjectMonthly, seq: int | None = None) -> dict[str, Any]:
        result = CamelCaseUtil.transform_result(row)
        update_time = getattr(row, 'update_time', 0) or 0
        result['updateTimeStr'] = timestamp_to_datetime(update_time, '%Y-%m-%d %H:%M:%S') if update_time else ''
        if seq is not None:
            result['seq'] = seq
        return result

    @classmethod
    async def get_project_monthly_list(
            cls, db: AsyncSession, query_object: ProjectMonthlyPageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """分页查询月度项目台账"""
        conditions = cls._build_conditions(query_object)
        query = (
            select(OaProjectMonthly)
            .where(*conditions)
            .order_by(OaProjectMonthly.stat_month.desc(), OaProjectMonthly.id.desc())
        )
        if is_page:
            total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
            offset = (query_object.page_num - 1) * query_object.page_size
            rows = (await db.execute(query.offset(offset).limit(query_object.page_size))).scalars().all()
            data = [
                cls._to_dict(row, (query_object.page_num - 1) * query_object.page_size + index + 1)
                for index, row in enumerate(rows)
            ]
            return PageModel[dict[str, Any]](
                rows=data,
                pageNum=query_object.page_num,
                pageSize=query_object.page_size,
                total=total,
                hasNext=query_object.page_num * query_object.page_size < total,
            )
        rows = (await db.execute(query)).scalars().all()
        return [
            cls._to_dict(row, index + 1)
            for index, row in enumerate(rows)
        ]

    @classmethod
    async def get_project_monthly_by_id(cls, db: AsyncSession, record_id: int) -> OaProjectMonthly | None:
        """根据ID查询详情"""
        result = await db.execute(
            select(OaProjectMonthly).where(OaProjectMonthly.id == record_id, OaProjectMonthly.delete_time == 0)
        )
        return result.scalars().first()

    @classmethod
    async def get_duplicate(
            cls, db: AsyncSession, stat_month: str, project_name: str, customer_name: str, exclude_id: int = 0
    ) -> OaProjectMonthly | None:
        """按唯一键校验重复（未删除记录）"""
        query = select(OaProjectMonthly).where(
            OaProjectMonthly.stat_month == stat_month,
            OaProjectMonthly.project_name == project_name,
            OaProjectMonthly.customer_name == customer_name,
            OaProjectMonthly.delete_time == 0,
        )
        if exclude_id:
            query = query.where(OaProjectMonthly.id != exclude_id)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def add_project_monthly(cls, db: AsyncSession, data: dict[str, Any]) -> OaProjectMonthly:
        """新增记录"""
        record = OaProjectMonthly(**data)
        db.add(record)
        await db.flush()
        return record

    @classmethod
    async def edit_project_monthly(cls, db: AsyncSession, record_id: int, data: dict[str, Any]) -> None:
        """编辑记录"""
        await db.execute(
            update(OaProjectMonthly)
            .where(OaProjectMonthly.id == record_id, OaProjectMonthly.delete_time == 0)
            .values(**data)
        )

    @classmethod
    async def delete_project_monthly(cls, db: AsyncSession, record_id: int) -> None:
        """逻辑删除"""
        await db.execute(
            update(OaProjectMonthly)
            .where(OaProjectMonthly.id == record_id)
            .values(delete_time=int(datetime.now().timestamp()), update_time=int(datetime.now().timestamp()))
        )
