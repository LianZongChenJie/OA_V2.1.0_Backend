from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.timeformat import format_timestamp, int_time
from decimal import Decimal


class OaLoanBaseModel(BaseModel):
    """借支基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    subject_id: int | None = Field(None, description='借支企业主体')
    code: str | None = Field(None, description='借支编码')
    title: str | None = Field(None, description='借款主题')
    cost: Decimal | None = Field(None, description='借支金额')
    types: int | None = Field(None, description='借支类型：1日常备用金,2项目预支款')
    loan_time: int | str | None = Field(None, description='预期借支日期')
    plan_time: int | str | None = Field(None, description='预计还款日期')
    content: str | None = Field(None, description='借支理由')
    admin_id: int | None = Field(None, description='借支人')
    did: int | None = Field(None, description='借支部门ID')
    balance_cost: Decimal | None = Field(None, description='已冲账金额')
    balance_status: int | None = Field(None, description='冲账状态 0待冲账,1部分冲账,2已冲账')
    project_id: int | None = Field(None, description='关联项目ID')
    file_ids: str | None = Field(None, description='附件ID，如:1,2,3')
    pay_status: int | None = Field(None, description='打款状态 0待打款,1已打款')
    pay_admin_id: int | None = Field(None, description='打款人ID')
    pay_time: int | str | None = Field(None, description='最后打款时间')
    back_status: int | None = Field(None, description='还款状态 0待还款,1已还款')
    back_admin_id: int | None = Field(None, description='还款操作人ID')
    back_time: int | str | None = Field(None, description='最后还款时间')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')
    delete_time: int | None = Field(None, description='删除时间')
    check_status: int | None = Field(None, description='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id: int | None = Field(None, description='审核流程id')
    check_step_sort: int | None = Field(None, description='当前审批步骤')
    check_uids: str | None = Field(None, description='当前审批人ID，如:1,2,3')
    check_last_uid: str | None = Field(None, description='上一审批人')
    check_history_uids: str | None = Field(None, description='历史审批人ID，如:1,2,3')
    check_copy_uids: str | None = Field(None, description='抄送人ID，如:1,2,3')
    check_time: int | str | None = Field(None, description='审核通过时间')

    @validator('*', pre=True)
    def empty_string_to_none(cls, v):
        if isinstance(v, str) and len(v.strip()) == 0:
            return None
        return v

    @field_serializer('loan_time')
    def serialize_loan_time(self, value: int) -> str:
        """序列化借支日期"""
        return format_timestamp(value)

    @field_serializer('plan_time')
    def serialize_plan_time(self, value: int) -> str:
        """序列化预计还款时间日期"""
        return format_timestamp(value)

    @field_serializer('pay_time')
    def serialize_pay_time(self, value: int) -> str:
        """序列化最后付款时间"""
        return format_timestamp(value)
    @field_serializer('back_time')
    def serialize_back_time(self, value: int) -> str:
        """序列化最后还款时间"""
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

class OaLoanQueryModel(OaLoanBaseModel):
    """借支查询VO"""

    begin_time: str | None = Field(None, description='创建时间开始时间')
    end_time: str | None = Field(None, description='创建时间结束时间')

class OaLoanPageQueryModel(OaLoanQueryModel):
    """借支分页VO"""
    page_num: int = Field(default = 1, description='页码')
    page_size: int = Field(default = 20, description='每页大小')

class OaLoanDetailModel(BaseModel):
    """借支详情VO"""
    info: OaLoanBaseModel = Field(None, description='借支详情')
    records: list[OaFlowRecordBaseModel] | None = Field(None, description='审批记录')
