import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_service_settlement.dao.service_customer_settlement_dao import ServiceCustomerSettlementDao
from module_service_settlement.entity.vo.service_customer_settlement_vo import (
    AddServiceCustomerSettlementModel,
    DeleteServiceCustomerSettlementModel,
    EditServiceCustomerSettlementModel,
    ServiceCustomerSettlementImportResponseModel,
    ServiceCustomerSettlementModel,
    ServiceCustomerSettlementPageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.log_util import logger
from utils.time_format_util import timestamp_to_datetime

IMPORT_HEADERS = [
    '序号',
    '年度',
    '月份',
    '客户名称',
    '姓名',
    '职位',
    '级别',
    '单价（元）',
    '实际出勤（天）',
    '请假（天）',
    '加班（天）',
    '调休（天）',
    '实际应结算费用（元）',
    '实际结算费用',
    '是否结算（是/否）',
    '备注',
]

HEADER_FIELD_MAP = {
    '序号': 'seq',
    '年度': 'stat_year',
    '月份': 'stat_month',
    '客户名称': 'customer_name',
    '姓名': 'employee_name',
    '职位': 'position_name',
    '级别': 'level_name',
    '单价（元）': 'unit_price',
    '实际出勤（天）': 'actual_attendance_days',
    '请假（天）': 'leave_days',
    '加班（天）': 'overtime_days',
    '调休（天）': 'comp_off_days',
    '实际应结算费用（元）': 'payable_amount',
    '实际结算费用': 'settled_amount',
    '是否结算（是/否）': 'is_settled',
    '备注': 'remark',
}

EXPORT_FIELD_MAP = {
    'seq': '序号',
    'statYear': '年度',
    'statMonth': '月份',
    'customerName': '客户名称',
    'employeeName': '姓名',
    'positionName': '职位',
    'levelName': '级别',
    'unitPrice': '单价（元）',
    'actualAttendanceDays': '实际出勤（天）',
    'leaveDays': '请假（天）',
    'overtimeDays': '加班（天）',
    'compOffDays': '调休（天）',
    'payableAmount': '实际应结算费用（元）',
    'settledAmount': '实际结算费用',
    'isSettled': '是否结算（是/否）',
    'remark': '备注',
}

DAY_FIELDS = [
    'actual_attendance_days',
    'leave_days',
    'overtime_days',
    'comp_off_days',
]

MONEY_FIELDS = [
    'unit_price',
    'payable_amount',
    'settled_amount',
]

BOOL_TRUE_VALUES = {'1', '是', 'y', 'yes', 'true'}
BOOL_FALSE_VALUES = {'', '0', '否', 'n', 'no', 'false'}


class ServiceCustomerSettlementService:
    """服务客户结算服务层"""

    @staticmethod
    def default_stat_year() -> int:
        """默认年度：当前年"""
        return date.today().year

    @staticmethod
    def _normalize_int(value: Any, field_label: str, min_value: int, max_value: int) -> int:
        raw = str(value if value is not None else '').strip().replace('月', '')
        if raw.endswith('.0'):
            raw = raw[:-2]
        if not raw or not re.fullmatch(r'-?\d+', raw):
            raise ServiceException(message=f'{field_label}必须为整数')
        number = int(raw)
        if number < min_value or number > max_value:
            raise ServiceException(message=f'{field_label}必须在 {min_value}~{max_value} 之间')
        return number

    @staticmethod
    def _normalize_bool(value: Any, field_label: str) -> int:
        raw = str(value if value is not None else '').strip().lower()
        if raw in BOOL_TRUE_VALUES:
            return 1
        if raw in BOOL_FALSE_VALUES:
            return 0
        raise ServiceException(message=f'{field_label}只能填写 是/否')

    @staticmethod
    def _normalize_decimal(value: Any, field_label: str, min_value: Decimal | None = None) -> Decimal:
        raw = str(value if value is not None else '').strip().replace(',', '').replace('￥', '').replace('¥', '')
        if raw == '':
            return Decimal('0.00')
        try:
            number = Decimal(raw)
        except InvalidOperation as exc:
            raise ServiceException(message=f'{field_label}数字格式不正确') from exc
        if min_value is not None and number < min_value:
            raise ServiceException(message=f'{field_label}不能小于 {min_value}')
        return number

    @staticmethod
    def _normalize_text(value: Any, field_label: str, max_length: int, required: bool = False) -> str:
        text = str(value if value is not None else '').strip()
        if required and not text:
            raise ServiceException(message=f'{field_label}不能为空')
        if len(text) > max_length:
            raise ServiceException(message=f'{field_label}不能超过 {max_length} 个字符')
        return text

    @classmethod
    def _normalize_query(cls, query_object: ServiceCustomerSettlementPageQueryModel) -> None:
        """归一化查询条件，兼容前端清空筛选时传入的空串"""
        year_value = str(query_object.stat_year if query_object.stat_year is not None else '').strip()
        if year_value:
            query_object.stat_year = cls._normalize_int(year_value, '年度', 1900, 2100)
        else:
            query_object.stat_year = cls.default_stat_year()

        month_value = str(query_object.stat_month if query_object.stat_month is not None else '').strip()
        query_object.stat_month = (
            cls._normalize_int(month_value, '月份', 1, 12) if month_value else None
        )

        settled_value = str(query_object.is_settled if query_object.is_settled is not None else '').strip()
        query_object.is_settled = (
            cls._normalize_bool(settled_value, '是否结算') if settled_value else None
        )

    @classmethod
    async def get_service_customer_settlement_list_services(
            cls, query_db: AsyncSession, query_object: ServiceCustomerSettlementPageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """查询服务客户结算列表"""
        cls._normalize_query(query_object)
        return await ServiceCustomerSettlementDao.get_service_customer_settlement_list(query_db, query_object, is_page)

    @classmethod
    async def service_customer_settlement_detail_services(
            cls, query_db: AsyncSession, record_id: int
    ) -> ServiceCustomerSettlementModel:
        """查询详情"""
        record = await ServiceCustomerSettlementDao.get_service_customer_settlement_by_id(query_db, record_id)
        if not record:
            raise ServiceException(message='记录不存在')
        data = CamelCaseUtil.transform_result(record)
        create_time = getattr(record, 'create_time', 0) or 0
        update_time = getattr(record, 'update_time', 0) or 0
        data['createTimeStr'] = timestamp_to_datetime(create_time, '%Y-%m-%d %H:%M:%S') if create_time else ''
        data['updateTimeStr'] = timestamp_to_datetime(update_time, '%Y-%m-%d %H:%M:%S') if update_time else ''
        return ServiceCustomerSettlementModel(**data)

    @classmethod
    async def add_service_customer_settlement_services(
            cls, query_db: AsyncSession, page_object: AddServiceCustomerSettlementModel, current_user_id: int
    ) -> CrudResponseModel:
        """新增记录"""
        stat_year = cls._normalize_int(page_object.stat_year, '年度', 1900, 2100)
        stat_month = cls._normalize_int(page_object.stat_month, '月份', 1, 12)
        customer_name = cls._normalize_text(page_object.customer_name, '客户名称', 255, required=True)
        employee_name = cls._normalize_text(page_object.employee_name, '姓名', 255, required=True)
        duplicate = await ServiceCustomerSettlementDao.get_duplicate(
            query_db, stat_year, stat_month, customer_name, employee_name
        )
        if duplicate:
            raise ServiceException(message='该年度月份下客户名称与姓名相同的记录已存在')

        current_time = int(datetime.now().timestamp())
        data = {
            'stat_year': stat_year,
            'stat_month': stat_month,
            'customer_name': customer_name,
            'employee_name': employee_name,
            'position_name': cls._normalize_text(page_object.position_name, '职位', 100),
            'level_name': cls._normalize_text(page_object.level_name, '级别', 100),
            'unit_price': cls._normalize_decimal(page_object.unit_price, '单价（元）', Decimal('0')),
            'actual_attendance_days': cls._normalize_decimal(
                page_object.actual_attendance_days, '实际出勤（天）', Decimal('0')
            ),
            'leave_days': cls._normalize_decimal(page_object.leave_days, '请假（天）', Decimal('0')),
            'overtime_days': cls._normalize_decimal(page_object.overtime_days, '加班（天）', Decimal('0')),
            'comp_off_days': cls._normalize_decimal(page_object.comp_off_days, '调休（天）', Decimal('0')),
            'payable_amount': cls._normalize_decimal(
                page_object.payable_amount, '实际应结算费用（元）', Decimal('0')
            ),
            'settled_amount': cls._normalize_decimal(page_object.settled_amount, '实际结算费用', Decimal('0')),
            'is_settled': cls._normalize_bool(page_object.is_settled if page_object.is_settled is not None else 0, '是否结算'),
            'remark': cls._normalize_text(page_object.remark, '备注', 1000),
            'admin_id': current_user_id,
            'create_time': current_time,
            'update_time': current_time,
            'delete_time': 0,
            'tenant_id': 1,
        }
        await ServiceCustomerSettlementDao.add_service_customer_settlement(query_db, data)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    async def edit_service_customer_settlement_services(
            cls, query_db: AsyncSession, page_object: EditServiceCustomerSettlementModel
    ) -> CrudResponseModel:
        """编辑记录"""
        if not page_object.id:
            raise ServiceException(message='记录ID不能为空')
        record = await ServiceCustomerSettlementDao.get_service_customer_settlement_by_id(query_db, page_object.id)
        if not record:
            raise ServiceException(message='记录不存在')

        # 年度、月份、客户名称、姓名、职位、级别为业务身份字段，编辑时以库内值为准
        stat_year = cls._normalize_int(record.stat_year, '年度', 1900, 2100)
        stat_month = cls._normalize_int(record.stat_month, '月份', 1, 12)
        customer_name = cls._normalize_text(record.customer_name, '客户名称', 255, required=True)
        employee_name = cls._normalize_text(record.employee_name, '姓名', 255, required=True)
        position_name = cls._normalize_text(record.position_name, '职位', 100)
        level_name = cls._normalize_text(record.level_name, '级别', 100)

        data = {
            'stat_year': stat_year,
            'stat_month': stat_month,
            'customer_name': customer_name,
            'employee_name': employee_name,
            'position_name': position_name,
            'level_name': level_name,
            'unit_price': cls._normalize_decimal(page_object.unit_price, '单价（元）', Decimal('0')),
            'actual_attendance_days': cls._normalize_decimal(
                page_object.actual_attendance_days, '实际出勤（天）', Decimal('0')
            ),
            'leave_days': cls._normalize_decimal(page_object.leave_days, '请假（天）', Decimal('0')),
            'overtime_days': cls._normalize_decimal(page_object.overtime_days, '加班（天）', Decimal('0')),
            'comp_off_days': cls._normalize_decimal(page_object.comp_off_days, '调休（天）', Decimal('0')),
            'payable_amount': cls._normalize_decimal(
                page_object.payable_amount, '实际应结算费用（元）', Decimal('0')
            ),
            'settled_amount': cls._normalize_decimal(page_object.settled_amount, '实际结算费用', Decimal('0')),
            'is_settled': cls._normalize_bool(
                page_object.is_settled if page_object.is_settled is not None else record.is_settled, '是否结算'
            ),
            'remark': cls._normalize_text(page_object.remark, '备注', 1000),
            'update_time': int(datetime.now().timestamp()),
        }
        await ServiceCustomerSettlementDao.edit_service_customer_settlement(query_db, page_object.id, data)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    async def delete_service_customer_settlement_services(
            cls, query_db: AsyncSession, page_object: DeleteServiceCustomerSettlementModel
    ) -> CrudResponseModel:
        """逻辑删除记录"""
        record = await ServiceCustomerSettlementDao.get_service_customer_settlement_by_id(query_db, page_object.id)
        if not record:
            raise ServiceException(message='记录不存在')
        await ServiceCustomerSettlementDao.delete_service_customer_settlement(query_db, page_object.id)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    def generate_import_template(cls) -> io.BytesIO:
        """生成导入模板（表头与页面一致）"""
        try:
            options = [{'是否结算（是/否）': ['是', '否']}]
            data = ExcelUtil.get_excel_template(IMPORT_HEADERS, ['是否结算（是/否）'], options)
            return io.BytesIO(data)
        except Exception as exc:
            logger.error(f'生成服务客户结算导入模板失败：{exc}', exc_info=True)
            raise ServiceException(message='生成导入模板失败') from exc

    @classmethod
    async def import_service_customer_settlement_services(
            cls, query_db: AsyncSession, file: UploadFile, current_user_id: int
    ) -> ServiceCustomerSettlementImportResponseModel:
        """批量导入服务客户结算"""
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise ServiceException(message='仅支持 Excel 文件（.xlsx/.xls）导入')

        try:
            contents = await file.read()
            frame = pd.read_excel(io.BytesIO(contents), header=0, dtype=str)
            frame.columns = [str(column).strip() for column in frame.columns]
            frame = frame.dropna(how='all').fillna('').rename(columns=HEADER_FIELD_MAP)
            records = frame.to_dict('records')
        except Exception as exc:
            logger.error(f'解析服务客户结算 Excel 失败：{exc}', exc_info=True)
            raise ServiceException(message='Excel 文件解析失败') from exc

        success_count = 0
        fail_data: list[dict] = []
        current_time = int(datetime.now().timestamp())

        for index, row in enumerate(records, start=2):
            try:
                stat_year = cls._normalize_int(row.get('stat_year', ''), '年度', 1900, 2100)
                stat_month = cls._normalize_int(row.get('stat_month', ''), '月份', 1, 12)
                customer_name = cls._normalize_text(row.get('customer_name', ''), '客户名称', 255, required=True)
                employee_name = cls._normalize_text(row.get('employee_name', ''), '姓名', 255, required=True)
                duplicate = await ServiceCustomerSettlementDao.get_duplicate(
                    query_db, stat_year, stat_month, customer_name, employee_name
                )
                if duplicate:
                    raise ServiceException(message='该年度月份下客户名称与姓名相同的记录已存在')

                data = {
                    'stat_year': stat_year,
                    'stat_month': stat_month,
                    'customer_name': customer_name,
                    'employee_name': employee_name,
                    'position_name': cls._normalize_text(row.get('position_name', ''), '职位', 100),
                    'level_name': cls._normalize_text(row.get('level_name', ''), '级别', 100),
                    'unit_price': cls._normalize_decimal(row.get('unit_price', ''), '单价（元）', Decimal('0')),
                    'actual_attendance_days': cls._normalize_decimal(
                        row.get('actual_attendance_days', ''), '实际出勤（天）', Decimal('0')
                    ),
                    'leave_days': cls._normalize_decimal(row.get('leave_days', ''), '请假（天）', Decimal('0')),
                    'overtime_days': cls._normalize_decimal(row.get('overtime_days', ''), '加班（天）', Decimal('0')),
                    'comp_off_days': cls._normalize_decimal(row.get('comp_off_days', ''), '调休（天）', Decimal('0')),
                    'payable_amount': cls._normalize_decimal(
                        row.get('payable_amount', ''), '实际应结算费用（元）', Decimal('0')
                    ),
                    'settled_amount': cls._normalize_decimal(
                        row.get('settled_amount', ''), '实际结算费用', Decimal('0')
                    ),
                    'is_settled': cls._normalize_bool(row.get('is_settled', ''), '是否结算'),
                    'remark': cls._normalize_text(row.get('remark', ''), '备注', 1000),
                    'admin_id': current_user_id,
                    'create_time': current_time,
                    'update_time': current_time,
                    'delete_time': 0,
                    'tenant_id': 1,
                }
                await ServiceCustomerSettlementDao.add_service_customer_settlement(query_db, data)
                success_count += 1
            except ServiceException as exc:  # noqa: PERF203
                fail_data.append({'row': index, 'reason': exc.message})
            except Exception as exc:
                fail_data.append({'row': index, 'reason': str(exc)})

        if success_count:
            await query_db.commit()
        else:
            await query_db.rollback()

        return ServiceCustomerSettlementImportResponseModel(
            is_success=True,
            message='导入完成',
            success_count=success_count,
            fail_count=len(fail_data),
            fail_data=fail_data or None,
        )

    @classmethod
    async def export_service_customer_settlement_services(
            cls, query_db: AsyncSession, query_object: ServiceCustomerSettlementPageQueryModel
    ) -> bytes:
        """按当前筛选条件导出 Excel"""
        cls._normalize_query(query_object)
        rows = await ServiceCustomerSettlementDao.get_service_customer_settlement_list(query_db, query_object, is_page=False)
        for row in rows:
            row['isSettled'] = '是' if row.get('isSettled') == 1 else '否'
        return ExcelUtil.export_list2excel(rows, EXPORT_FIELD_MAP)
