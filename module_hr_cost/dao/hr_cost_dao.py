from datetime import datetime
from typing import Any

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_hr_cost.entity.do.hr_cost_do import OaHrCost
from module_hr_cost.entity.vo.hr_cost_vo import HrCostPageQueryModel
from utils.common_util import CamelCaseUtil
from utils.time_format_util import timestamp_to_datetime


class HrCostDao:
    """人力总成本数据库操作层"""

    @staticmethod
    def _build_conditions(
            query_object: HrCostPageQueryModel, org_ids: list[int] | None = None
    ) -> list[Any]:
        conditions: list[Any] = [OaHrCost.delete_time == 0]
        if query_object.stat_month:
            conditions.append(OaHrCost.stat_month == query_object.stat_month)
        if query_object.org_id:
            if org_ids:
                conditions.append(OaHrCost.org_id.in_(org_ids))
            else:
                conditions.append(OaHrCost.org_id == query_object.org_id)
        if query_object.city_id:
            conditions.append(OaHrCost.city_id == query_object.city_id)
        if query_object.employee_status:
            conditions.append(OaHrCost.employee_status == query_object.employee_status)
        if query_object.employee_name:
            conditions.append(OaHrCost.employee_name.like(f'%{query_object.employee_name}%'))
        if query_object.keywords:
            keyword = f'%{query_object.keywords}%'
            conditions.append(
                OaHrCost.employee_name.like(keyword)
                | OaHrCost.id_card.like(keyword)
                | OaHrCost.project_name.like(keyword)
            )
        return conditions

    @classmethod
    def _to_dict(cls, row: OaHrCost, seq: int | None = None) -> dict[str, Any]:
        result = CamelCaseUtil.transform_result(row)
        create_time = getattr(row, 'create_time', 0) or 0
        update_time = getattr(row, 'update_time', 0) or 0
        result['createTimeStr'] = timestamp_to_datetime(create_time, '%Y-%m-%d %H:%M:%S') if create_time else ''
        result['updateTimeStr'] = timestamp_to_datetime(update_time, '%Y-%m-%d %H:%M:%S') if update_time else ''
        if seq is not None:
            result['seq'] = seq
        return result

    @classmethod
    async def get_hr_cost_list(
            cls, db: AsyncSession, query_object: HrCostPageQueryModel,
            org_ids: list[int] | None = None, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """查询人力总成本列表"""
        conditions = cls._build_conditions(query_object, org_ids)
        query = (
            select(OaHrCost)
            .where(*conditions)
            .order_by(OaHrCost.stat_month.desc(), OaHrCost.org_id, OaHrCost.id.desc())
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
    async def get_hr_cost_by_id(cls, db: AsyncSession, record_id: int) -> OaHrCost | None:
        """根据ID查询详情"""
        result = await db.execute(
            select(OaHrCost).where(OaHrCost.id == record_id, OaHrCost.delete_time == 0)
        )
        return result.scalars().first()

    @classmethod
    async def get_duplicate(cls, db: AsyncSession, stat_month: str, id_card: str, exclude_id: int = 0) -> OaHrCost | None:
        """按月份 + 身份证号校验重复"""
        query = select(OaHrCost).where(
            OaHrCost.stat_month == stat_month,
            OaHrCost.id_card == id_card,
            OaHrCost.delete_time == 0,
        )
        if exclude_id:
            query = query.where(OaHrCost.id != exclude_id)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def add_hr_cost(cls, db: AsyncSession, data: dict[str, Any]) -> OaHrCost:
        """新增记录"""
        record = OaHrCost(**data)
        db.add(record)
        await db.flush()
        return record

    @classmethod
    async def edit_hr_cost(cls, db: AsyncSession, record_id: int, data: dict[str, Any]) -> None:
        """编辑记录"""
        await db.execute(
            update(OaHrCost)
            .where(OaHrCost.id == record_id, OaHrCost.delete_time == 0)
            .values(**data)
        )

    @classmethod
    async def delete_hr_cost(cls, db: AsyncSession, record_id: int) -> None:
        """逻辑删除"""
        current_time = int(datetime.now().timestamp())
        await db.execute(
            update(OaHrCost)
            .where(OaHrCost.id == record_id)
            .values(delete_time=current_time, update_time=current_time)
        )

    @classmethod
    async def get_summary(
            cls,
            db: AsyncSession,
            query_object: HrCostPageQueryModel,
            org_ids: list[int] | None,
            group_by: str,
    ) -> list[dict[str, Any]]:
        """按组织架构或城市汇总"""
        conditions = cls._build_conditions(query_object, org_ids)
        if group_by == 'org':
            id_col = OaHrCost.org_id
            name_col = OaHrCost.org_name
        else:
            id_col = OaHrCost.city_id
            name_col = OaHrCost.city_name

        aggregate_fields = {
            'grossSalary': func.sum(OaHrCost.gross_salary),
            'socialPersonalTotal': func.sum(OaHrCost.social_personal_total),
            'housingFundPersonal': func.sum(OaHrCost.housing_fund_personal),
            'incomeTaxCount': func.sum(case((OaHrCost.income_tax != 0, 1), else_=0)),
            'bankPayAmount': func.sum(OaHrCost.bank_pay_amount),
            'socialCompanyTotal': func.sum(OaHrCost.social_company_total),
            'housingFundCompany': func.sum(OaHrCost.housing_fund_company),
            'companyTotalCost': func.sum(OaHrCost.company_total_cost),
            'customerFeeTaxIncluded': func.sum(OaHrCost.customer_fee_tax_included),
            'taxExcludedRevenue': func.sum(OaHrCost.customer_fee_tax_included / 1.06),
            'grossProfit': func.sum(OaHrCost.gross_profit),
        }
        query = select(
            id_col.label('id'),
            name_col.label('name'),
            *(expression.label(key) for key, expression in aggregate_fields.items()),
        ).where(*conditions).group_by(id_col, name_col).order_by(name_col)
        result = await db.execute(query)
        rows = []
        for row in result.mappings().all():
            item = {'name': row['name'], 'id': row['id']}
            for key in aggregate_fields:
                value = row[key] or 0
                item[key] = value
            rows.append(item)

        if rows:
            total = {'name': '合计', 'id': 0}
            for key in aggregate_fields:
                total[key] = sum((row[key] or 0) for row in rows)
            rows.append(total)
        return rows
