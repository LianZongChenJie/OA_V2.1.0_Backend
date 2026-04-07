from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.timeformat import format_timestamp
from decimal import Decimal


class OaInvoiceBaseModel(BaseModel):
    """发票基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    id: int | None = Field(None, description='ID')
    code: str | None = Field(None, description='发票号码')
    customer_id: int | None = Field(None, description='关联客户ID')
    contract_id: int | None = Field(None, description='关联合同协议ID')
    project_id: int | None = Field(None, description='关联项目ID')
    amount: Decimal | None = Field(None, description='发票金额')
    did: int | None = Field(None, description='发票申请部门')
    admin_id: int | None = Field(None, description='发票申请人')
    open_status: int | None = Field(None, description='开票状态：0未开票 1已开票 2已作废')
    open_admin_id: int | None = Field(None, description='发票开具人')
    open_time: int | str | None = Field(None, description='发票开具时间')
    delivery: str | None = Field(None, description='快递单号')
    types: int | None = Field(None, description='抬头类型：1企业2个人')
    invoice_type: int | None = Field(None, description='发票类型：1增值税专用发票,2普通发票,3专用发票')
    invoice_subject: int | None = Field(None, description='关联发票主体ID')
    invoice_title: str | None = Field(None, description='开票抬头')
    invoice_tax: str | None = Field(None, description='纳税人识别号')
    invoice_phone: str | None = Field(None, description='电话号码')
    invoice_address: str | None = Field(None, description='地址')
    invoice_bank: str | None = Field(None, description='开户银行')
    invoice_account: str | None = Field(None, description='银行账号')
    invoice_banking: str | None = Field(None, description='银行营业网点')
    file_ids: str | None = Field(None, description='附件ID，如:1,2,3')
    other_file_ids: str | None = Field(None, description='其他附件ID，如:1,2,3')
    remark: str | None = Field(None, description='备注')
    enter_amount: Decimal | None = Field(None, description='已到账金额')
    enter_status: int | None = Field(None, description='回款状态：0未回款 1部分回款 2全部回款')
    enter_time: int | str | None = Field(None, description='最新回款时间')
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
    check_time: int | None = Field(None, description='审核通过时间')

    @field_serializer('open_time')
    def serialize_open_time(self, value: int) -> str:
        """序列化开票时间"""
        return format_timestamp(value)

    @field_serializer('enter_time')
    def serialize_enter_time(self, value: int) -> str:
        """序列化回款时间"""
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

class OaInvoiceQueryModel(OaInvoiceBaseModel):
    """OaInvoiceQueryModel"""
    begin_time: str | None= Field(None, description='创建时间开始')
    end_time: str | None= Field(None, description='创建时间结束')
    is_code: bool | None = Field(None, description='是否为发票回款is_code 1发票回款，0非发票回款is_code')

class OaInvoicePageQueryModel(OaInvoiceQueryModel):
    """OaInvoicePageQueryModel"""
    page_num: int = Field(1, description="页码")
    page_size: int = Field(20, description="每页大小")

class OaInvoiceDetailModel(BaseModel):
    """OaInvoiceDetailModel"""
    info: OaInvoiceBaseModel| None = Field(..., description='发票信息')
    records: list[OaFlowRecordBaseModel] | None  = Field(..., description='发票流程记录')


class OaInvoiceIncomeBaseModel(BaseModel):
    """发票到账记录基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    id: int | None = Field(None, description='ID')
    invoice_id: int | None = Field(None, description='发票ID')
    amount: Decimal | None = Field(None, description='到账金额')
    admin_id: int | None = Field(None, description='到账登记人')
    enter_time: int | str | None = Field(None, description='到账时间')
    remarks: str | None = Field(None, description='备注')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')
    status: int | None = Field(None, description='状态：-1删除 0禁用 1正常 6作废')

class OaInvoiceIncomeDetailModel(BaseModel):
    """OaInvoiceIncomeDetailModel"""
    info: OaInvoiceBaseModel | None = Field(..., description='发票信息')
    income_list: list[OaInvoiceIncomeBaseModel] | None = Field(..., description='发票到账记录')
