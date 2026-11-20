import io
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_project_monthly.dao.project_monthly_dao import ProjectMonthlyDao
from module_project_monthly.entity.vo.project_monthly_vo import (
    AddProjectMonthlyModel,
    DeleteProjectMonthlyModel,
    EditProjectMonthlyModel,
    ProjectMonthlyImportResponseModel,
    ProjectMonthlyModel,
    ProjectMonthlyPageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.log_util import logger
from utils.time_format_util import timestamp_to_datetime

IMPORT_HEADERS = [
    '序号',
    '年度',
    '客户名称',
    '项目名称',
    '合同是否签订',
    '预计投入成本',
    '实际投入成本',
    '预计项目利润',
    '实际项目利润',
    '合同收款约定',
    '实际开票金额',
    '实际收款金额',
    '是否结项',
    '创建时间',
    '更新时间',
]

HEADER_FIELD_MAP = {
    '年度': 'stat_month',
    '序号': 'seq',
    '客户名称': 'customer_name',
    '项目名称': 'project_name',
    '合同是否签订': 'contract_signed',
    '预计投入成本': 'planned_cost',
    '实际投入成本': 'actual_cost',
    '预计项目利润': 'planned_profit',
    '实际项目利润': 'actual_profit',
    '合同收款约定': 'collection_agreement',
    '实际开票金额': 'invoiced_amount',
    '实际收款金额': 'received_amount',
    '是否结项': 'project_closed',
    '创建时间': 'create_time_str',
    '更新时间': 'update_time_str',
}

EXPORT_FIELD_MAP = {
    'seq': '序号',
    'statMonth': '年度',
    'customerName': '客户名称',
    'projectName': '项目名称',
    'contractSigned': '合同是否签订',
    'plannedCost': '预计投入成本',
    'actualCost': '实际投入成本',
    'plannedProfit': '预计项目利润',
    'actualProfit': '实际项目利润',
    'collectionAgreement': '合同收款约定',
    'invoicedAmount': '实际开票金额',
    'receivedAmount': '实际收款金额',
    'projectClosed': '是否结项',
    'createTimeStr': '创建时间',
    'updateTimeStr': '更新时间',
}

MONEY_FIELDS = [
    'planned_cost',
    'actual_cost',
    'planned_profit',
    'actual_profit',
    'invoiced_amount',
    'received_amount',
]

BOOL_TRUE_VALUES = {'1', '是', 'y', 'yes', 'true', '已签订', '已结项'}


class ProjectMonthlyService:
    """月度项目台账服务层"""

    @staticmethod
    def default_stat_month() -> str:
        """默认统计月份：上一个月 YYYY-MM"""
        first_day_this_month = date.today().replace(day=1)
        return (first_day_this_month - timedelta(days=1)).strftime('%Y-%m')

    @classmethod
    async def get_project_monthly_list_services(
            cls, query_db: AsyncSession, query_object: ProjectMonthlyPageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """查询台账列表"""
        if not query_object.stat_month:
            query_object.stat_month = cls.default_stat_month()
        return await ProjectMonthlyDao.get_project_monthly_list(query_db, query_object, is_page)

    @classmethod
    async def project_monthly_detail_services(cls, query_db: AsyncSession, record_id: int) -> ProjectMonthlyModel:
        """查询台账详情"""
        record = await ProjectMonthlyDao.get_project_monthly_by_id(query_db, record_id)
        if not record:
            raise ServiceException(message='记录不存在')
        data = CamelCaseUtil.transform_result(record)
        create_time = getattr(record, 'create_time', 0) or 0
        update_time = getattr(record, 'update_time', 0) or 0
        data['createTimeStr'] = timestamp_to_datetime(create_time, '%Y-%m-%d %H:%M:%S') if create_time else ''
        data['updateTimeStr'] = timestamp_to_datetime(update_time, '%Y-%m-%d %H:%M:%S') if update_time else ''
        return ProjectMonthlyModel(**data)

    @staticmethod
    def _normalize_stat_month(value: str) -> str:
        stat_month = str(value or '').strip()
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', stat_month):
            raise ServiceException(message='年度/统计月份格式必须为 YYYY-MM')
        return stat_month

    @staticmethod
    def _normalize_bool(value: Any, field_label: str) -> int:
        raw = str(value if value is not None else '').strip().lower()
        if raw in BOOL_TRUE_VALUES:
            return 1
        if raw in {'', '0', '否', 'n', 'no', 'false', '未签订', '未结项'}:
            return 0
        raise ServiceException(message=f'{field_label}只能填写 是/否')

    @staticmethod
    def _normalize_money(value: Any, field_label: str) -> Decimal:
        raw = str(value if value is not None else '').strip().replace(',', '').replace('￥', '').replace('¥', '')
        if raw == '':
            return Decimal('0.00')
        try:
            return Decimal(raw)
        except InvalidOperation as exc:
            raise ServiceException(message=f'{field_label}金额格式不正确') from exc

    @classmethod
    async def add_project_monthly_services(
            cls, query_db: AsyncSession, page_object: AddProjectMonthlyModel, current_user_id: int
    ) -> CrudResponseModel:
        """新增台账记录"""
        stat_month = cls._normalize_stat_month(page_object.stat_month or '')
        customer_name = (page_object.customer_name or '').strip()
        project_name = (page_object.project_name or '').strip()
        if not customer_name:
            raise ServiceException(message='客户名称不能为空')
        if not project_name:
            raise ServiceException(message='项目名称不能为空')

        duplicate = await ProjectMonthlyDao.get_duplicate(query_db, stat_month, project_name, customer_name)
        if duplicate:
            raise ServiceException(message='该月份下客户名称与项目名称相同的记录已存在')

        current_time = int(datetime.now().timestamp())
        data = {
            'stat_month': stat_month,
            'customer_name': customer_name,
            'project_name': project_name,
            'contract_signed': page_object.contract_signed or 0,
            'planned_cost': page_object.planned_cost or Decimal('0.00'),
            'actual_cost': page_object.actual_cost or Decimal('0.00'),
            'planned_profit': page_object.planned_profit or Decimal('0.00'),
            'actual_profit': page_object.actual_profit or Decimal('0.00'),
            'collection_agreement': (page_object.collection_agreement or '').strip(),
            'invoiced_amount': page_object.invoiced_amount or Decimal('0.00'),
            'received_amount': page_object.received_amount or Decimal('0.00'),
            'project_closed': page_object.project_closed or 0,
            'project_id': page_object.project_id or 0,
            'remark': (page_object.remark or '').strip(),
            'admin_id': current_user_id,
            'create_time': current_time,
            'update_time': current_time,
            'delete_time': 0,
            'tenant_id': 1,
        }
        await ProjectMonthlyDao.add_project_monthly(query_db, data)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    async def edit_project_monthly_services(
            cls, query_db: AsyncSession, page_object: EditProjectMonthlyModel
    ) -> CrudResponseModel:
        """编辑台账记录"""
        if not page_object.id:
            raise ServiceException(message='记录ID不能为空')
        record = await ProjectMonthlyDao.get_project_monthly_by_id(query_db, page_object.id)
        if not record:
            raise ServiceException(message='记录不存在')

        stat_month = cls._normalize_stat_month(page_object.stat_month or record.stat_month or '')
        customer_name = (page_object.customer_name or record.customer_name or '').strip()
        project_name = (page_object.project_name or record.project_name or '').strip()
        if not customer_name:
            raise ServiceException(message='客户名称不能为空')
        if not project_name:
            raise ServiceException(message='项目名称不能为空')

        duplicate = await ProjectMonthlyDao.get_duplicate(
            query_db, stat_month, project_name, customer_name, exclude_id=page_object.id
        )
        if duplicate:
            raise ServiceException(message='该月份下客户名称与项目名称相同的记录已存在')

        data = page_object.model_dump(exclude={'id', 'admin_id', 'create_time', 'delete_time'}, exclude_unset=True)
        data.pop('seq', None)
        data.pop('create_time_str', None)
        data.pop('update_time_str', None)
        data['stat_month'] = stat_month
        data['customer_name'] = customer_name
        data['project_name'] = project_name
        data['update_time'] = int(datetime.now().timestamp())
        await ProjectMonthlyDao.edit_project_monthly(query_db, page_object.id, data)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    async def delete_project_monthly_services(
            cls, query_db: AsyncSession, page_object: DeleteProjectMonthlyModel
    ) -> CrudResponseModel:
        """逻辑删除台账记录"""
        record = await ProjectMonthlyDao.get_project_monthly_by_id(query_db, page_object.id)
        if not record:
            raise ServiceException(message='记录不存在')
        await ProjectMonthlyDao.delete_project_monthly(query_db, page_object.id)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    def generate_import_template(cls) -> io.BytesIO:
        """生成导入模板（表头与页面列一致）"""
        try:
            options = [
                {'合同是否签订': ['是', '否'], '是否结项': ['是', '否']},
            ]
            data = ExcelUtil.get_excel_template(IMPORT_HEADERS, ['合同是否签订', '是否结项'], options)
            return io.BytesIO(data)
        except Exception as exc:
            logger.error(f'生成月度项目台账导入模板失败：{exc}', exc_info=True)
            raise ServiceException(message='生成导入模板失败') from exc

    @classmethod
    async def import_project_monthly_services(
            cls, query_db: AsyncSession, file: UploadFile, current_user_id: int
    ) -> ProjectMonthlyImportResponseModel:
        """批量导入台账记录"""
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise ServiceException(message='仅支持 Excel 文件（.xlsx/.xls）导入')

        try:
            contents = await file.read()
            frame = pd.read_excel(io.BytesIO(contents), header=0, dtype=str)
            frame.columns = [str(column).strip() for column in frame.columns]
            frame = frame.dropna(how='all').fillna('').rename(columns=HEADER_FIELD_MAP)
            records = frame.to_dict('records')
        except Exception as exc:
            logger.error(f'解析月度项目台账 Excel 失败：{exc}', exc_info=True)
            raise ServiceException(message='Excel 文件解析失败') from exc

        success_count = 0
        fail_data: list[dict] = []
        current_time = int(datetime.now().timestamp())

        for index, row in enumerate(records, start=2):
            try:
                stat_month = cls._normalize_stat_month(row.get('stat_month', ''))
                customer_name = str(row.get('customer_name', '') or '').strip()
                project_name = str(row.get('project_name', '') or '').strip()
                if not customer_name:
                    raise ServiceException(message='客户名称不能为空')
                if not project_name:
                    raise ServiceException(message='项目名称不能为空')

                duplicate = await ProjectMonthlyDao.get_duplicate(query_db, stat_month, project_name, customer_name)
                if duplicate:
                    raise ServiceException(message='该月份下客户名称与项目名称相同的记录已存在')

                data = {
                    'stat_month': stat_month,
                    'customer_name': customer_name,
                    'project_name': project_name,
                    'contract_signed': cls._normalize_bool(row.get('contract_signed'), '合同是否签订'),
                    'planned_cost': cls._normalize_money(row.get('planned_cost'), '预计投入成本'),
                    'actual_cost': cls._normalize_money(row.get('actual_cost'), '实际投入成本'),
                    'planned_profit': cls._normalize_money(row.get('planned_profit'), '预计项目利润'),
                    'actual_profit': cls._normalize_money(row.get('actual_profit'), '实际项目利润'),
                    'collection_agreement': str(row.get('collection_agreement', '') or '').strip(),
                    'invoiced_amount': cls._normalize_money(row.get('invoiced_amount'), '实际开票金额'),
                    'received_amount': cls._normalize_money(row.get('received_amount'), '实际收款金额'),
                    'project_closed': cls._normalize_bool(row.get('project_closed'), '是否结项'),
                    'project_id': 0,
                    'remark': '',
                    'admin_id': current_user_id,
                    'create_time': current_time,
                    'update_time': current_time,
                    'delete_time': 0,
                    'tenant_id': 1,
                }
                await ProjectMonthlyDao.add_project_monthly(query_db, data)
                success_count += 1
            except ServiceException as exc:  # noqa: PERF203
                fail_data.append({'row': index, 'reason': exc.message})
            except Exception as exc:
                fail_data.append({'row': index, 'reason': str(exc)})

        if success_count:
            await query_db.commit()
        else:
            await query_db.rollback()

        return ProjectMonthlyImportResponseModel(
            is_success=True,
            message='导入完成',
            success_count=success_count,
            fail_count=len(fail_data),
            fail_data=fail_data or None,
        )

    @classmethod
    async def export_project_monthly_services(
            cls, query_db: AsyncSession, query_object: ProjectMonthlyPageQueryModel
    ) -> bytes:
        """按当前筛选条件导出 Excel"""
        if not query_object.stat_month:
            query_object.stat_month = cls.default_stat_month()
        rows = await ProjectMonthlyDao.get_project_monthly_list(query_db, query_object, is_page=False)
        for row in rows:
            row['contractSigned'] = '是' if row.get('contractSigned') == 1 else '否'
            row['projectClosed'] = '是' if row.get('projectClosed') == 1 else '否'
        return ExcelUtil.export_list2excel(rows, EXPORT_FIELD_MAP)
