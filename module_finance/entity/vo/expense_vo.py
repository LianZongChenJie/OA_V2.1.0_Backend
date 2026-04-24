from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

from module_finance.entity.vo.expense_interfix_vo import OaExpenseInterfixBaseModel
from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.timeformat import format_timestamp
from decimal import Decimal


class OaExpenseBaseModel(BaseModel):
    """报销基础VO"""
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel)

    id: int | None= Field(None, description='ID')
    subject_id: int | None= Field(None, description='报销企业主体')
    code: str | None= Field(None, description='报销编码')
    cost:  Decimal | None= Field(None, description='报销总金额')
    income_month: int | str | None= Field(None, description='入账月份')
    expense_time: int| str | None= Field(None, description='原始单据日期')
    admin_id: int | None= Field(None, description='报销人')
    did: int | None= Field(None, description='报销部门ID')
    loan_id: int | None= Field(None, description='关联借支ID')
    balance_cost:  Decimal | None= Field(None, description='冲账金额')
    pay_amount:  Decimal | None= Field(None, description='需打款金额')
    project_id: int | None= Field(None, description='关联项目ID')
    file_ids: str | None= Field(None, description='附件ID，如:1,2,3')
    pay_status: int | None= Field(None, description='打款状态 0待打款,1已打款')
    pay_admin_id: int | None= Field(None, description='打款人ID')
    pay_time: int | None= Field(None, description='最后打款时间')
    remark: str | None= Field(None, description='备注')
    create_time: int | None= Field(None, description='创建时间')
    update_time: int | None= Field(None, description='更新时间')
    delete_time: int | None= Field(None, description='删除时间')
    check_status: int | None= Field(None, description='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id: int | None= Field(None, description='审核流程id')
    check_step_sort: int | None= Field(None, description='当前审批步骤')
    check_uids: str | None= Field(None, description='当前审批人ID，如:1,2,3')
    check_last_uid: str | None= Field(None, description='上一审批人')
    check_history_uids: str | None= Field(None, description='历史审批人ID，如:1,2,3')
    check_copy_uids: str | None= Field(None, description='抄送人ID，如:1,2,3')
    check_time: int | None= Field(None, description='审核通过时间')

    @field_serializer('expense_time')
    def serialize_expense_time(self, value: int) -> str:
        """序列化原始单据日期"""
        return format_timestamp(value)

    @field_serializer('pay_time')
    def serialize_pay_time(self, value: int) -> str:
        """序列化最后付款时间"""
        return format_timestamp(value)

    @field_serializer('create_time')
    def serialize_create_time(self, value: int) -> str:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: int) -> str:
        """序列化更新时间"""
        return format_timestamp(value)

    @field_serializer('delete_time')
    def serialize_delete_time(self, value: int) -> str:
        """序列化删除时间"""
        return format_timestamp(value)

    @field_serializer('check_time')
    def serialize_check_time(self, value: int) -> str:
        """序列化审核时间"""
        return format_timestamp(value)

class OaExpenseQueryModel(OaExpenseBaseModel):
    """报销查询VO"""
    begin_time: str | None= Field(None, description='创建时间开始')
    end_time: str | None= Field(None, description='创建时间结束')

class OaExpensePageQueryModel(OaExpenseQueryModel):
    """报销分页查询VO"""
    page_num: int = Field(1, description="页码")
    page_size: int = Field(20, description="每页大小")

class OaExpenseDetailModel(OaExpenseBaseModel):
    interfix: list[OaExpenseInterfixBaseModel] | None = Field([], description="费用明细")
    flow_records: list[OaFlowRecordBaseModel] | None = Field([], description="流水记录")