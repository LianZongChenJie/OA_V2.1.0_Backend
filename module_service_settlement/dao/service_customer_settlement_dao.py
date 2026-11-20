from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_service_settlement.entity.do.service_customer_settlement_do import OaServiceCustomerSettlement
from module_service_settlement.entity.vo.service_customer_settlement_vo import ServiceCustomerSettlementPageQueryModel
from utils.common_util import CamelCaseUtil
from utils.time_format_util import timestamp_to_datetime


class ServiceCustomerSettlementDao:
    """服务客户结算数据库操作层"""

    @staticmethod
    def _build_conditions(query_object: ServiceCustomerSettlementPageQueryModel) -> list[Any]:
        conditions: list[Any] = [OaServiceCustomerSettlement.delete_time == 0]
        if query_object.stat_year:
            conditions.append(OaServiceCustomerSettlement.stat_year == query_object.stat_year)
        if query_object.stat_month:
            conditions.append(OaServiceCustomerSettlement.stat_month == query_object.stat_month)
        if query_object.customer_name:
            conditions.append(OaServiceCustomerSettlement.customer_name.like(f'%{query_object.customer_name}%'))
        if query_object.employee_name:
            conditions.append(OaServiceCustomerSettlement.employee_name.like(f'%{query_object.employee_name}%'))
        if query_object.is_settled is not None:
            conditions.append(OaServiceCustomerSettlement.is_settled == query_object.is_settled)
        if query_object.keywords:
            keyword = f'%{query_object.keywords}%'
            conditions.append(
                OaServiceCustomerSettlement.customer_name.like(keyword)
                | OaServiceCustomerSettlement.employee_name.like(keyword)
            )
        return conditions

    @classmethod
    def _to_dict(cls, row: OaServiceCustomerSettlement, seq: int | None = None) -> dict[str, Any]:
        result = CamelCaseUtil.transform_result(row)
        create_time = getattr(row, 'create_time', 0) or 0
        update_time = getattr(row, 'update_time', 0) or 0
        result['createTimeStr'] = timestamp_to_datetime(create_time, '%Y-%m-%d %H:%M:%S') if create_time else ''
        result['updateTimeStr'] = timestamp_to_datetime(update_time, '%Y-%m-%d %H:%M:%S') if update_time else ''
        if seq is not None:
            result['seq'] = seq
        return result

    @classmethod
    async def get_service_customer_settlement_list(
            cls, db: AsyncSession, query_object: ServiceCustomerSettlementPageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """分页查询服务客户结算"""
        conditions = cls._build_conditions(query_object)
        query = (
            select(OaServiceCustomerSettlement)
            .where(*conditions)
            .order_by(
                OaServiceCustomerSettlement.stat_year.desc(),
                OaServiceCustomerSettlement.stat_month.desc(),
                OaServiceCustomerSettlement.id.desc(),
            )
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
        return [cls._to_dict(row, index + 1) for index, row in enumerate(rows)]

    @classmethod
    async def get_service_customer_settlement_by_id(
            cls, db: AsyncSession, record_id: int
    ) -> OaServiceCustomerSettlement | None:
        """根据ID查询详情"""
        result = await db.execute(
            select(OaServiceCustomerSettlement).where(
                OaServiceCustomerSettlement.id == record_id,
                OaServiceCustomerSettlement.delete_time == 0,
            )
        )
        return result.scalars().first()

    @classmethod
    async def get_duplicate(
            cls,
            db: AsyncSession,
            stat_year: int,
            stat_month: int,
            customer_name: str,
            employee_name: str,
            exclude_id: int = 0,
    ) -> OaServiceCustomerSettlement | None:
        """按唯一键校验重复（未删除记录）"""
        query = select(OaServiceCustomerSettlement).where(
            OaServiceCustomerSettlement.stat_year == stat_year,
            OaServiceCustomerSettlement.stat_month == stat_month,
            OaServiceCustomerSettlement.customer_name == customer_name,
            OaServiceCustomerSettlement.employee_name == employee_name,
            OaServiceCustomerSettlement.delete_time == 0,
        )
        if exclude_id:
            query = query.where(OaServiceCustomerSettlement.id != exclude_id)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def add_service_customer_settlement(
            cls, db: AsyncSession, data: dict[str, Any]
    ) -> OaServiceCustomerSettlement:
        """新增记录"""
        record = OaServiceCustomerSettlement(**data)
        db.add(record)
        await db.flush()
        return record

    @classmethod
    async def edit_service_customer_settlement(
            cls, db: AsyncSession, record_id: int, data: dict[str, Any]
    ) -> None:
        """编辑记录"""
        await db.execute(
            update(OaServiceCustomerSettlement)
            .where(
                OaServiceCustomerSettlement.id == record_id,
                OaServiceCustomerSettlement.delete_time == 0,
            )
            .values(**data)
        )

    @classmethod
    async def delete_service_customer_settlement(cls, db: AsyncSession, record_id: int) -> None:
        """逻辑删除"""
        current_time = int(datetime.now().timestamp())
        await db.execute(
            update(OaServiceCustomerSettlement)
            .where(OaServiceCustomerSettlement.id == record_id)
            .values(delete_time=current_time, update_time=current_time)
        )
