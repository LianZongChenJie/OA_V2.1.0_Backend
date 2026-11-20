import io
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from fastapi import UploadFile
from openpyxl.utils import get_column_letter
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_hr_cost.dao.hr_cost_dao import HrCostDao
from module_hr_cost.entity.vo.hr_cost_vo import (
    AddHrCostModel,
    EditHrCostModel,
    HrCostImportResponseModel,
    HrCostModel,
    HrCostPageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.log_util import logger
from utils.time_format_util import timestamp_to_datetime

REVENUE_TAX_FACTOR = Decimal('1.06')
ENTRY_RECORD_OPTIONS = ('新入职', '重新入职')

IMPORT_HEADERS = [
    '序号', '员工状态', '城市', '月份', '组织架构', '姓名', '身份证号码', '入职日期', '入职记录', '目前所在项目',
    '合同工资', '算薪比例', '基本工资', '绩效工资', '岗位工资', '考勤（天）', '客户费用单',
    '电脑补助（加）', '工作日餐补（加）', '奖金（加）', '补助（加）', '扣款（迟到/请假/工会）（减）',
    '其他扣款（社保补基差额）（减）', '未扣五险一金薪资总额', '养老个人部分', '医疗个人部分', '失业个人部分',
    '社保个人合计', '公积金个人部分', '扣除五险一金税前工资', '个税代扣代缴', '银行实际支付金额',
    '养老单位部分', '失业单位部分', '工伤单位部分', '（医疗+生育）单位部分', '社保单位合计',
    '公积金单位部分', '社保总合计', '公积金总合计', '企业总成本', '社保基数', '公积金基数', '备注', '毛利', '个税申报金额',
]

HEADER_FIELD_MAP = {
    '序号': 'seq', '员工状态': 'employee_status', '城市': 'city_name', '月份': 'stat_month',
    '组织架构': 'org_name', '姓名': 'employee_name', '身份证号码': 'id_card',
    '入职日期': 'entry_date', '入职记录': 'entry_record_date', '目前所在项目': 'project_name',
    '合同工资': 'contract_salary', '算薪比例': 'salary_ratio', '100%or80%': 'salary_ratio', '基本工资': 'base_salary',
    '绩效工资': 'performance_salary', '岗位工资': 'post_salary', '考勤（天）': 'attendance_days',
    '客户费用单': 'customer_fee_tax_included', '电脑补助（加）': 'computer_subsidy',
    '工作日餐补（加）': 'meal_subsidy', '奖金（加）': 'bonus', '补助（加）': 'subsidy',
    '扣款（迟到/请假/工会）（减）': 'deduction', '其他扣款（社保补基差额）（减）': 'other_deduction',
    '未扣五险一金薪资总额': 'gross_salary', '养老个人部分': 'pension_personal',
    '医疗个人部分': 'medical_personal', '失业个人部分': 'unemployment_personal',
    '社保个人合计': 'social_personal_total', '公积金个人部分': 'housing_fund_personal',
    '扣除五险一金税前工资': 'taxable_salary', '个税代扣代缴': 'income_tax',
    '银行实际支付金额': 'bank_pay_amount', '养老单位部分': 'pension_company',
    '失业单位部分': 'unemployment_company', '工伤单位部分': 'injury_company',
    '（医疗+生育）单位部分': 'medical_maternity_company', '社保单位合计': 'social_company_total',
    '公积金单位部分': 'housing_fund_company', '社保总合计': 'social_total',
    '公积金总合计': 'housing_fund_total', '企业总成本': 'company_total_cost',
    '社保基数': 'social_base', '公积金基数': 'housing_fund_base', '备注': 'remark',
    '毛利': 'gross_profit', '个税申报金额': 'tax_declaration_amount',
}

EXPORT_FIELD_MAP = {
    'seq': '序号', 'employeeStatus': '员工状态', 'cityName': '城市', 'statMonth': '月份',
    'orgName': '组织架构', 'employeeName': '姓名', 'idCard': '身份证号码', 'entryDateStr': '入职日期',
    'entryRecordDateStr': '入职记录', 'projectName': '目前所在项目', 'contractSalary': '合同工资',
    'salaryRatio': '算薪比例', 'baseSalary': '基本工资', 'performanceSalary': '绩效工资',
    'postSalary': '岗位工资', 'attendanceDays': '考勤（天）', 'customerFeeTaxIncluded': '客户费用单',
    'computerSubsidy': '电脑补助（加）', 'mealSubsidy': '工作日餐补（加）', 'bonus': '奖金（加）',
    'subsidy': '补助（加）', 'deduction': '扣款（迟到/请假/工会）（减）',
    'otherDeduction': '其他扣款（社保补基差额）（减）', 'grossSalary': '未扣五险一金薪资总额',
    'pensionPersonal': '养老个人部分', 'medicalPersonal': '医疗个人部分',
    'unemploymentPersonal': '失业个人部分', 'socialPersonalTotal': '社保个人合计',
    'housingFundPersonal': '公积金个人部分', 'taxableSalary': '扣除五险一金税前工资',
    'incomeTax': '个税代扣代缴', 'bankPayAmount': '银行实际支付金额', 'pensionCompany': '养老单位部分',
    'unemploymentCompany': '失业单位部分', 'injuryCompany': '工伤单位部分',
    'medicalMaternityCompany': '（医疗+生育）单位部分', 'socialCompanyTotal': '社保单位合计',
    'housingFundCompany': '公积金单位部分', 'socialTotal': '社保总合计',
    'housingFundTotal': '公积金总合计', 'companyTotalCost': '企业总成本', 'socialBase': '社保基数',
    'housingFundBase': '公积金基数', 'remark': '备注', 'grossProfit': '毛利',
    'taxDeclarationAmount': '个税申报金额',
}

EXPORT_TOTAL_FIELDS = [
    'contractSalary', 'baseSalary', 'performanceSalary', 'postSalary', 'attendanceDays',
    'customerFeeTaxIncluded', 'computerSubsidy', 'mealSubsidy', 'bonus', 'subsidy',
    'deduction', 'otherDeduction', 'grossSalary', 'pensionPersonal', 'medicalPersonal',
    'unemploymentPersonal', 'socialPersonalTotal', 'housingFundPersonal', 'taxableSalary',
    'incomeTax', 'bankPayAmount', 'pensionCompany', 'unemploymentCompany', 'injuryCompany',
    'medicalMaternityCompany', 'socialCompanyTotal', 'housingFundCompany', 'socialTotal',
    'housingFundTotal', 'companyTotalCost', 'socialBase', 'housingFundBase',
    'grossProfit', 'taxDeclarationAmount',
]

ORG_SUMMARY_FIELD_MAP = {
    'name': '组织架构', 'grossSalary': '未扣五险一金薪资总额',
    'socialPersonalTotal': '社保个人合计', 'housingFundPersonal': '公积金个人部分',
    'incomeTaxCount': '计数项:个税代扣代缴', 'bankPayAmount': '银行实际支付金额',
    'socialCompanyTotal': '社保单位合计', 'housingFundCompany': '公积金单位部分',
    'companyTotalCost': '企业总成本', 'customerFeeTaxIncluded': '客户费用单（含税）',
    'taxExcludedRevenue': '不含税收入', 'grossProfit': '毛利',
}

CITY_SUMMARY_FIELD_MAP = {
    'name': '城市', 'grossSalary': '未扣五险一金薪资总额',
    'socialPersonalTotal': '社保个人合计', 'housingFundPersonal': '公积金个人部分',
    'incomeTaxCount': '计数项:个税代扣代缴', 'bankPayAmount': '银行实际支付金额',
    'socialCompanyTotal': '社保单位合计', 'housingFundCompany': '公积金单位部分',
    'companyTotalCost': '企业总成本', 'customerFeeTaxIncluded': '客户费用单',
    'taxExcludedRevenue': '不含税收入', 'grossProfit': '毛利',
}

AMOUNT_FIELDS = [
    'contract_salary', 'salary_ratio', 'base_salary', 'performance_salary', 'post_salary',
    'attendance_days', 'customer_fee_tax_included', 'computer_subsidy', 'meal_subsidy',
    'bonus', 'subsidy', 'deduction', 'other_deduction', 'pension_personal', 'medical_personal',
    'unemployment_personal', 'housing_fund_personal', 'income_tax', 'pension_company',
    'unemployment_company', 'injury_company', 'medical_maternity_company', 'housing_fund_company',
    'social_base', 'housing_fund_base',
]

TEXT_FIELDS = {
    'employee_status': ('员工状态', 20),
    'project_name': ('目前所在项目', 255),
    'remark': ('备注', 1000),
}


class HrCostCalculateUtil:
    """人力成本计算工具（固定 1.06 口径）"""

    @staticmethod
    def decimal(value: Any, label: str) -> Decimal:
        raw = str(value if value is not None else '').strip().replace(',', '').replace('￥', '').replace('¥', '')
        if raw == '':
            return Decimal('0')
        try:
            return Decimal(raw)
        except InvalidOperation as exc:
            raise ServiceException(message=f'{label}数字格式不正确') from exc

    @classmethod
    def calculate(cls, data: dict[str, Any]) -> dict[str, Any]:
        value = {key: cls.decimal(data.get(key), key) for key in AMOUNT_FIELDS}
        gross_salary = (
            value['base_salary'] + value['performance_salary'] + value['post_salary']
            + value['computer_subsidy'] + value['meal_subsidy'] + value['bonus'] + value['subsidy']
            - value['deduction'] - value['other_deduction']
        )
        social_personal_total = value['pension_personal'] + value['medical_personal'] + value['unemployment_personal']
        taxable_salary = gross_salary - social_personal_total - value['housing_fund_personal']
        bank_pay_amount = taxable_salary - value['income_tax']
        social_company_total = (
            value['pension_company'] + value['unemployment_company']
            + value['injury_company'] + value['medical_maternity_company']
        )
        social_total = social_personal_total + social_company_total
        housing_fund_total = value['housing_fund_personal'] + value['housing_fund_company']
        company_total_cost = gross_salary + social_company_total + value['housing_fund_company']
        tax_excluded_revenue = value['customer_fee_tax_included'] / REVENUE_TAX_FACTOR
        gross_profit = tax_excluded_revenue - company_total_cost

        data.update({
            'gross_salary': gross_salary,
            'social_personal_total': social_personal_total,
            'taxable_salary': taxable_salary,
            'bank_pay_amount': bank_pay_amount,
            'social_company_total': social_company_total,
            'social_total': social_total,
            'housing_fund_total': housing_fund_total,
            'company_total_cost': company_total_cost,
            'tax_excluded_revenue': tax_excluded_revenue,
            'gross_profit': gross_profit,
            'tax_declaration_amount': taxable_salary,
        })
        return data


class HrCostService:
    """人力总成本服务层"""

    @staticmethod
    def last_import_month() -> str:
        """默认导入月份：上个月"""
        first_day = date.today().replace(day=1)
        return (first_day - timedelta(days=1)).strftime('%Y-%m')

    @classmethod
    def allowed_import_months(cls) -> list[str]:
        """允许选择的导入月份：当月和上个月"""
        return [date.today().strftime('%Y-%m'), cls.last_import_month()]

    @staticmethod
    def _normalize_month(value: Any) -> str:
        if isinstance(value, datetime):
            return value.strftime('%Y-%m')
        if isinstance(value, date):
            return value.strftime('%Y-%m')
        raw = str(value if value is not None else '').strip().replace('/', '-').replace('年', '-').replace('月', '')
        match = re.match(r'^(\d{4})-(\d{1,2})', raw)
        if match:
            return f'{int(match.group(1)):04d}-{int(match.group(2)):02d}'
        if re.fullmatch(r'\d{6}', raw):
            return f'{raw[:4]}-{raw[4:]}'
        raise ServiceException(message='月份格式不正确，应为 YYYY-MM')

    @staticmethod
    def _normalize_date(value: Any, label: str) -> int:
        if value is None or str(value).strip() == '':
            return 0
        if isinstance(value, datetime):
            return int(value.timestamp())
        if isinstance(value, date):
            return int(datetime(value.year, value.month, value.day).timestamp())
        raw = str(value).strip()
        if re.fullmatch(r'\d+(\.\d+)?', raw):
            base = datetime(1899, 12, 30)
            return int((base + timedelta(days=float(raw))).timestamp())
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S'):
            try:
                return int(datetime.strptime(raw, fmt).timestamp())
            except ValueError:
                continue
        raise ServiceException(message=f'{label}日期格式不正确')

    @staticmethod
    def _normalize_text(value: Any, label: str, max_length: int, required: bool = False) -> str:
        text = str(value if value is not None else '').strip()
        if required and not text:
            raise ServiceException(message=f'{label}不能为空')
        if len(text) > max_length:
            raise ServiceException(message=f'{label}不能超过 {max_length} 个字符')
        return text

    @staticmethod
    def _normalize_entry_record(value: Any) -> str:
        text = str(value if value is not None else '').strip()
        if not text:
            return ''
        if text not in ENTRY_RECORD_OPTIONS:
            raise ServiceException(message=f'入职记录只能为 {" / ".join(ENTRY_RECORD_OPTIONS)}')
        return text

    @classmethod
    def _normalize_query(cls, query_object: HrCostPageQueryModel) -> None:
        month = str(query_object.stat_month if query_object.stat_month is not None else '').strip()
        query_object.stat_month = cls._normalize_month(month) if month else datetime.now().strftime('%Y-%m')
        org = str(query_object.org_id if query_object.org_id is not None else '').strip()
        query_object.org_id = int(org) if org.isdigit() else None
        city = str(query_object.city_id if query_object.city_id is not None else '').strip()
        query_object.city_id = int(city) if city.isdigit() else None
        include_children = str(query_object.include_children if query_object.include_children is not None else '1').strip()
        query_object.include_children = 0 if include_children in ('0', 'false', 'False') else 1

    @classmethod
    async def _resolve_org_ids(
            cls, db: AsyncSession, query_object: HrCostPageQueryModel
    ) -> list[int] | None:
        if not query_object.org_id:
            return None
        if not query_object.include_children:
            return [int(query_object.org_id)]
        rows = (await db.execute(text(
            'SELECT dept_id, ancestors FROM sys_dept WHERE del_flag = "0"'
        ))).mappings().all()
        org_id = int(query_object.org_id)
        ids = {org_id}
        for row in rows:
            ancestors = str(row['ancestors'] or '').split(',')
            if str(org_id) in ancestors:
                ids.add(int(row['dept_id']))
        return list(ids)

    @classmethod
    async def _get_dept_name(cls, db: AsyncSession, dept_id: int) -> str:
        row = (await db.execute(text(
            'SELECT dept_name FROM sys_dept WHERE dept_id = :dept_id AND del_flag = "0"'
        ), {'dept_id': dept_id})).mappings().first()
        if not row:
            raise ServiceException(message='组织架构不存在')
        return str(row['dept_name'])

    @classmethod
    async def _get_area_name(cls, db: AsyncSession, area_id: int) -> str:
        row = (await db.execute(text(
            'SELECT name, shortname, level FROM oa_area WHERE id = :area_id'
        ), {'area_id': area_id})).mappings().first()
        if not row or int(row['level'] or 0) != 2:
            raise ServiceException(message='城市不存在或非城市级节点')
        return str(row['shortname'] or row['name'])

    @classmethod
    async def _find_dept_id(cls, db: AsyncSession, name: str) -> int:
        row = (await db.execute(text(
            'SELECT dept_id FROM sys_dept WHERE dept_name = :name AND del_flag = "0" LIMIT 1'
        ), {'name': name})).mappings().first()
        if not row:
            raise ServiceException(message=f'组织架构“{name}”不在 sys_dept 中')
        return int(row['dept_id'])

    @classmethod
    async def _find_area_id(cls, db: AsyncSession, name: str) -> int:
        normalized = name.replace('市', '').strip()
        row = (await db.execute(text(
            'SELECT id FROM oa_area WHERE level = 2 AND (name = :name OR shortname = :name '
            'OR name LIKE :pattern OR shortname LIKE :pattern) LIMIT 1'
        ), {'name': name, 'pattern': f'{normalized}%'})).mappings().first()
        if not row:
            raise ServiceException(message=f'城市“{name}”不在 oa_area 城市级节点中')
        return int(row['id'])

    @staticmethod
    def _build_time_strings(data: dict[str, Any]) -> dict[str, Any]:
        entry_date = int(data.get('entryDate') or data.get('entry_date') or 0)
        data['entryDateStr'] = timestamp_to_datetime(entry_date, '%Y-%m-%d') if entry_date else ''
        data['entryRecordDateStr'] = data.get('entryRecordDate') or data.get('entry_record_date') or ''
        return data

    @classmethod
    async def _build_input_data(
            cls, db: AsyncSession, page_object: Any, current_time: int, current_user_id: int
    ) -> dict[str, Any]:
        stat_month = cls._normalize_month(page_object.stat_month)
        id_card = cls._normalize_text(page_object.id_card, '身份证号码', 32, required=True).upper()
        employee_name = cls._normalize_text(page_object.employee_name, '姓名', 100, required=True)
        org_id = int(page_object.org_id or 0)
        city_id = int(page_object.city_id or 0)
        if not org_id:
            raise ServiceException(message='组织架构不能为空')
        if not city_id:
            raise ServiceException(message='城市不能为空')
        org_name = await cls._get_dept_name(db, org_id)
        city_name = await cls._get_area_name(db, city_id)

        data = {
            'stat_month': stat_month,
            'employee_status': cls._normalize_text(page_object.employee_status, '员工状态', 20),
            'city_id': city_id,
            'city_name': city_name,
            'org_id': org_id,
            'org_name': org_name,
            'employee_name': employee_name,
            'id_card': id_card,
            'entry_date': cls._normalize_date(page_object.entry_date, '入职日期'),
            'entry_record_date': cls._normalize_entry_record(page_object.entry_record_date),
            'project_name': cls._normalize_text(page_object.project_name, '目前所在项目', 255),
            'remark': cls._normalize_text(page_object.remark, '备注', 1000),
            'admin_id': current_user_id,
            'create_time': current_time,
            'update_time': current_time,
            'delete_time': 0,
            'tenant_id': 1,
        }
        for field in AMOUNT_FIELDS:
            data[field] = HrCostCalculateUtil.decimal(getattr(page_object, field, None), field)
        return HrCostCalculateUtil.calculate(data)

    @classmethod
    async def get_hr_cost_list_services(
            cls, db: AsyncSession, query_object: HrCostPageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        cls._normalize_query(query_object)
        org_ids = await cls._resolve_org_ids(db, query_object)
        rows = await HrCostDao.get_hr_cost_list(db, query_object, org_ids, is_page)
        if isinstance(rows, PageModel):
            for row in rows.rows:
                cls._build_time_strings(row)
        else:
            for row in rows:
                cls._build_time_strings(row)
        return rows

    @classmethod
    async def hr_cost_detail_services(cls, db: AsyncSession, record_id: int) -> HrCostModel:
        record = await HrCostDao.get_hr_cost_by_id(db, record_id)
        if not record:
            raise ServiceException(message='记录不存在')
        data = CamelCaseUtil.transform_result(record)
        cls._build_time_strings(data)
        return HrCostModel(**data)

    @classmethod
    async def add_hr_cost_services(
            cls, db: AsyncSession, page_object: AddHrCostModel, current_user_id: int
    ) -> CrudResponseModel:
        current_time = int(datetime.now().timestamp())
        data = await cls._build_input_data(db, page_object, current_time, current_user_id)
        duplicate = await HrCostDao.get_duplicate(db, data['stat_month'], data['id_card'])
        if duplicate:
            raise ServiceException(message='该月份 + 身份证号的记录已存在')
        await HrCostDao.add_hr_cost(db, data)
        await db.commit()
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    async def edit_hr_cost_services(cls, db: AsyncSession, page_object: EditHrCostModel) -> CrudResponseModel:
        if not page_object.id:
            raise ServiceException(message='记录ID不能为空')
        record = await HrCostDao.get_hr_cost_by_id(db, page_object.id)
        if not record:
            raise ServiceException(message='记录不存在')

        page_object.stat_month = record.stat_month
        page_object.id_card = record.id_card
        page_object.employee_name = record.employee_name
        page_object.org_id = record.org_id
        page_object.city_id = record.city_id

        current_time = int(datetime.now().timestamp())
        data = await cls._build_input_data(db, page_object, current_time, record.admin_id or 0)
        data.pop('create_time', None)
        data.pop('admin_id', None)
        data['update_time'] = current_time
        await HrCostDao.edit_hr_cost(db, page_object.id, data)
        await db.commit()
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    async def delete_hr_cost_services(cls, db: AsyncSession, record_id: int) -> CrudResponseModel:
        record = await HrCostDao.get_hr_cost_by_id(db, record_id)
        if not record:
            raise ServiceException(message='记录不存在')
        await HrCostDao.delete_hr_cost(db, record_id)
        await db.commit()
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def get_filter_options_services(cls, db: AsyncSession) -> dict[str, Any]:
        dept_rows = (await db.execute(text(
            'SELECT dept_id, parent_id, dept_name, order_num FROM sys_dept WHERE del_flag = "0" '
            'ORDER BY parent_id, order_num'
        ))).mappings().all()
        dept_nodes = {
            int(row['dept_id']): {'id': int(row['dept_id']), 'label': str(row['dept_name']), 'children': []}
            for row in dept_rows
        }
        dept_tree = []
        for row in dept_rows:
            node = dept_nodes[int(row['dept_id'])]
            parent_id = int(row['parent_id'] or 0)
            if parent_id in dept_nodes:
                dept_nodes[parent_id]['children'].append(node)
            else:
                dept_tree.append(node)

        area_rows = (await db.execute(text(
            'SELECT id, pid, name, shortname, level FROM oa_area WHERE level <= 2 ORDER BY id'
        ))).mappings().all()
        area_nodes = {
            int(row['id']): {
                'id': int(row['id']),
                'label': str(row['shortname'] or row['name']),
                'children': [],
            }
            for row in area_rows
        }
        area_tree = []
        for row in area_rows:
            node = area_nodes[int(row['id'])]
            parent_id = int(row['pid'] or 0)
            if parent_id in area_nodes:
                area_nodes[parent_id]['children'].append(node)
            else:
                area_tree.append(node)
        return {'deptTree': dept_tree, 'areaTree': area_tree}

    @staticmethod
    def _build_import_formula_map() -> dict[str, str]:
        def cell(header: str) -> str:
            return f'{get_column_letter(IMPORT_HEADERS.index(header) + 1)}{{row}}'

        def count(*headers: str) -> str:
            return 'COUNT(' + ','.join(cell(header) for header in headers) + ')'

        gross_headers = (
            '基本工资', '绩效工资', '岗位工资', '电脑补助（加）', '工作日餐补（加）',
            '奖金（加）', '补助（加）', '扣款（迟到/请假/工会）（减）', '其他扣款（社保补基差额）（减）',
        )
        personal_insurance_headers = ('养老个人部分', '医疗个人部分', '失业个人部分')
        company_insurance_headers = (
            '养老单位部分', '失业单位部分', '工伤单位部分', '（医疗+生育）单位部分',
        )

        return {
            '未扣五险一金薪资总额': (
                f'IF({count(*gross_headers)}=0,"",'
                f'{cell("基本工资")}+{cell("绩效工资")}+{cell("岗位工资")}'
                f'+{cell("电脑补助（加）")}+{cell("工作日餐补（加）")}+{cell("奖金（加）")}'
                f'+{cell("补助（加）")}-{cell("扣款（迟到/请假/工会）（减）")}'
                f'-{cell("其他扣款（社保补基差额）（减）")})'
            ),
            '社保个人合计': (
                f'IF({count(*personal_insurance_headers)}=0,"",'
                f'{"+".join(cell(header) for header in personal_insurance_headers)})'
            ),
            '扣除五险一金税前工资': (
                f'IF({count("未扣五险一金薪资总额", "社保个人合计", "公积金个人部分")}=0,"",'
                f'{cell("未扣五险一金薪资总额")}-{cell("社保个人合计")}-{cell("公积金个人部分")})'
            ),
            '银行实际支付金额': (
                f'IF({count("扣除五险一金税前工资", "个税代扣代缴")}=0,"",'
                f'{cell("扣除五险一金税前工资")}-{cell("个税代扣代缴")})'
            ),
            '社保单位合计': (
                f'IF({count(*company_insurance_headers)}=0,"",'
                f'{"+".join(cell(header) for header in company_insurance_headers)})'
            ),
            '社保总合计': (
                f'IF({count("社保个人合计", "社保单位合计")}=0,"",'
                f'{cell("社保个人合计")}+{cell("社保单位合计")})'
            ),
            '公积金总合计': (
                f'IF({count("公积金个人部分", "公积金单位部分")}=0,"",'
                f'{cell("公积金个人部分")}+{cell("公积金单位部分")})'
            ),
            '企业总成本': (
                f'IF({count("未扣五险一金薪资总额", "社保单位合计", "公积金单位部分")}=0,"",'
                f'{cell("未扣五险一金薪资总额")}+{cell("社保单位合计")}+{cell("公积金单位部分")})'
            ),
            '毛利': (
                f'IF({count("客户费用单", "企业总成本")}=0,"",'
                f'{cell("客户费用单")}/{REVENUE_TAX_FACTOR}-{cell("企业总成本")})'
            ),
            '个税申报金额': (
                f'IF({count("扣除五险一金税前工资")}=0,"",'
                f'{cell("扣除五险一金税前工资")})'
            ),
        }

    @classmethod
    def generate_import_template(cls) -> io.BytesIO:
        try:
            data = ExcelUtil.get_excel_template(
                IMPORT_HEADERS,
                ['入职记录', '算薪比例', '员工状态'],
                [
                    {'入职记录': list(ENTRY_RECORD_OPTIONS)},
                    {'算薪比例': ['0.8', '1']},
                    {'员工状态': ['在职', '离职']},
                ],
                formula_map=cls._build_import_formula_map(),
                formula_rows=500,
            )
            return io.BytesIO(data)
        except Exception as exc:
            logger.error(f'生成人力成本导入模板失败：{exc}', exc_info=True)
            raise ServiceException(message='生成导入模板失败') from exc

    @classmethod
    async def import_hr_cost_services(
            cls, db: AsyncSession, file: UploadFile, current_user_id: int, selected_month: str | None = None
    ) -> HrCostImportResponseModel:
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise ServiceException(message='仅支持 Excel 文件（.xlsx/.xls）导入')

        if not selected_month or not str(selected_month).strip():
            raise ServiceException(message='请选择导入月份')
        target_month = cls._normalize_month(selected_month)
        if target_month not in cls.allowed_import_months():
            raise ServiceException(message='仅支持选择当月或上个月导入')
        try:
            contents = await file.read()
            excel_file = pd.ExcelFile(io.BytesIO(contents))
            raw_frame = None
            header_row = None
            for sheet_name in excel_file.sheet_names:
                candidate = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, dtype=str)
                for index in range(min(10, len(candidate))):
                    values = [str(value).strip() for value in candidate.iloc[index].tolist()]
                    if '组织架构' in values and '身份证号码' in values:
                        raw_frame = candidate
                        header_row = index
                        break
                if header_row is not None:
                    break
            if header_row is None or raw_frame is None:
                raise ServiceException(message='未找到明细表头，请确保某个工作表包含“组织架构”和“身份证号码”列')

            columns = []
            for index, column in enumerate(raw_frame.iloc[header_row].tolist()):
                name = str(column).strip()
                columns.append('' if name in ('nan', 'None') else name or f'_empty_{index}')
            frame = raw_frame.iloc[header_row + 1:].copy()
            frame.columns = columns
            frame = frame.dropna(how='all').fillna('').rename(columns=HEADER_FIELD_MAP)

            records: list[dict] = []
            for excel_row, row in enumerate(frame.to_dict('records'), start=header_row + 2):
                values = [str(value).strip() for value in row.values() if str(value).strip()]
                if not values:
                    continue
                if any(value in ('合计', '总计') for value in values):
                    continue
                if any(value.startswith('备注：') or value.startswith('备注:') for value in values):
                    continue
                if not str(row.get('id_card', '')).strip() and not str(row.get('employee_name', '')).strip():
                    continue
                row['_excel_row'] = excel_row
                records.append(row)
        except ServiceException:
            raise
        except Exception as exc:
            logger.error(f'解析人力成本 Excel 失败：{exc}', exc_info=True)
            raise ServiceException(message='Excel 文件解析失败') from exc

        success_count = 0
        overwrite_count = 0
        fail_data: list[dict] = []
        current_time = int(datetime.now().timestamp())
        dept_cache: dict[str, int] = {}
        area_cache: dict[str, int] = {}

        for row in records:
            index = int(row.get('_excel_row', 0))
            try:
                stat_month = cls._normalize_month(row.get('stat_month', ''))
                if stat_month != target_month:
                    raise ServiceException(message=f'仅支持导入所选月份（{target_month}）的数据')

                org_name = cls._normalize_text(row.get('org_name', ''), '组织架构', 100, required=True)
                city_name = cls._normalize_text(row.get('city_name', ''), '城市', 100, required=True)
                if org_name not in dept_cache:
                    dept_cache[org_name] = await cls._find_dept_id(db, org_name)
                if city_name not in area_cache:
                    area_cache[city_name] = await cls._find_area_id(db, city_name)
                row['org_id'] = dept_cache[org_name]
                row['city_id'] = area_cache[city_name]

                id_card = cls._normalize_text(row.get('id_card', ''), '身份证号码', 32, required=True).upper()
                duplicate = await HrCostDao.get_duplicate(db, stat_month, id_card)

                data = {
                    'stat_month': stat_month,
                    'employee_status': cls._normalize_text(row.get('employee_status', ''), '员工状态', 20),
                    'city_id': int(row['city_id']),
                    'city_name': city_name,
                    'org_id': int(row['org_id']),
                    'org_name': org_name,
                    'employee_name': cls._normalize_text(row.get('employee_name', ''), '姓名', 100, required=True),
                    'id_card': id_card,
                    'entry_date': cls._normalize_date(row.get('entry_date', ''), '入职日期'),
                    'entry_record_date': cls._normalize_entry_record(row.get('entry_record_date', '')),
                    'project_name': cls._normalize_text(row.get('project_name', ''), '目前所在项目', 255),
                    'remark': cls._normalize_text(row.get('remark', ''), '备注', 1000),
                    'admin_id': current_user_id,
                    'create_time': current_time,
                    'update_time': current_time,
                    'delete_time': 0,
                    'tenant_id': 1,
                }
                for field in AMOUNT_FIELDS:
                    data[field] = HrCostCalculateUtil.decimal(row.get(field, ''), field)
                HrCostCalculateUtil.calculate(data)

                if duplicate:
                    update_data = {
                        key: value for key, value in data.items()
                        if key not in ('admin_id', 'create_time', 'delete_time', 'tenant_id')
                    }
                    update_data['update_time'] = current_time
                    await HrCostDao.edit_hr_cost(db, duplicate.id, update_data)
                    overwrite_count += 1
                else:
                    await HrCostDao.add_hr_cost(db, data)
                success_count += 1
            except ServiceException as exc:  # noqa: PERF203
                fail_data.append({'row': index, 'reason': exc.message})
            except Exception as exc:
                fail_data.append({'row': index, 'reason': str(exc)})

        if success_count:
            await db.commit()
        else:
            await db.rollback()
        return HrCostImportResponseModel(
            is_success=True,
            message=f'导入完成，覆盖 {overwrite_count} 条',
            success_count=success_count,
            fail_count=len(fail_data),
            fail_data=fail_data or None,
        )

    @classmethod
    async def get_summary_services(
            cls, db: AsyncSession, query_object: HrCostPageQueryModel, group_by: str
    ) -> list[dict[str, Any]]:
        cls._normalize_query(query_object)
        org_ids = await cls._resolve_org_ids(db, query_object)
        return await HrCostDao.get_summary(db, query_object, org_ids, group_by)

    @classmethod
    async def export_hr_cost_services(
            cls, db: AsyncSession, query_object: HrCostPageQueryModel
    ) -> bytes:
        cls._normalize_query(query_object)
        org_ids = await cls._resolve_org_ids(db, query_object)
        rows = await HrCostDao.get_hr_cost_list(db, query_object, org_ids, is_page=False)
        for row in rows:
            cls._build_time_strings(row)
        if rows:
            total_row = {key: '' for key in EXPORT_FIELD_MAP}
            total_row['employeeStatus'] = '合计'
            for field in EXPORT_TOTAL_FIELDS:
                total_row[field] = float(sum((Decimal(str(row.get(field) or 0)) for row in rows), Decimal('0')))
            rows.append(total_row)
        return ExcelUtil.export_list2excel(rows, EXPORT_FIELD_MAP)

    @classmethod
    async def export_summary_services(
            cls, db: AsyncSession, query_object: HrCostPageQueryModel, group_by: str
    ) -> bytes:
        rows = await cls.get_summary_services(db, query_object, group_by)
        field_map = ORG_SUMMARY_FIELD_MAP if group_by == 'org' else CITY_SUMMARY_FIELD_MAP
        return ExcelUtil.export_list2excel(rows, field_map)
