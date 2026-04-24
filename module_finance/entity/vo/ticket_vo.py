from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.timeformat import format_timestamp
from decimal import Decimal


class OaTicketBaseModel(BaseModel):
    """收票基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    code: str | None = Field(None, description='发票号码')
    supplier_id: int | None = Field(None, description='关联供应商ID')
    purchase_id: int | None = Field(None, description='关联采购合同协议ID')
    customer_id: int | None = Field(None, description='关联客户ID')
    project_id: int | None = Field(None, description='关联项目ID')
    amount: Decimal | None = Field(None, description='发票金额')
    did: int | None = Field(None, description='发票接受部门')
    admin_id: int | None = Field(None, description='发票接受人')
    open_status: int | None = Field(None, description='开票状态：1正常 2已作废')
    open_time: int | str |None = Field(None, description='发票开具时间')
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
    pay_amount: Decimal | None = Field(None, description='已付款金额')
    cash_type: int | None = Field(None, description='付款类型：1银行,2现金,3支付宝,4微信,5汇票,6支票,7托收,8其他')
    pay_status: int | None = Field(None, description='付款状态：0未付款 1部分付款 2全部付款')
    pay_time: int | None = Field(None, description='最新付款时间')
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

    @field_serializer('pay_time')
    def serialize_pay_time(self, value: int) -> str:
        """序列化付款时间"""
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
class OaTicketQueryModel(OaTicketBaseModel):
    """收票查询VO"""
    begin_time: str | None = Field(None, description='查询时间开始时间')
    end_time: str | None = Field(None, description='查询时间结束时间')
    is_code: bool | None = Field(None, description='是否室有发票付款 1是，0不是')

class OaTicketPageQueryModel(OaTicketQueryModel):

    page_num: int = Field(1, description='页码')
    page_size: int = Field(20, description='每页条数')

class OaTicketDetailModel(BaseModel):
    """收票审核详情VO"""
    ticket: OaTicketBaseModel | None = Field(None, description='收票信息')
    flow_records: list[OaFlowRecordBaseModel] | None = Field([], description='审核记录')



# -------------------------------------- 付款详情 ----------------------------------------------
class OaTicketPaymentBaseModel(BaseModel):
    """收票付款记录基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    ticket_id: int | None = Field(None, description='发票ID')
    amount: Decimal | None = Field(None, description='付款金额')
    admin_id: int | None = Field(None, description='付款登记人')
    pay_time: int | None = Field(None, description='付款时间')
    remarks: str | None = Field(None, description='备注')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')
    status: int | None = Field(None, description='状态：-1删除 0禁用 1正常 6作废')

class OaTicketPayMentDetailModel(BaseModel):
    """收票付款详情VO"""
    ticket: OaTicketBaseModel | None = Field(None, description='收票信息')
    payments: list[OaTicketPaymentBaseModel] | None = Field([], description='付款记录')
