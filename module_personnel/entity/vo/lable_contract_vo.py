from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel
from decimal import Decimal
from utils.timeformat import format_timestamp
from pydantic import field_serializer
from typing import Optional, List
class OaLaborContractBaseModel(BaseModel):
    """员工合同 VO - 用于数据展示"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None= Field(default=None, description='主键ID')
    renewal_pid: int | None= Field(default=None, description='续签母合同')
    change_pid: int | None= Field(default=None, description='变更母合同')
    uid: int | None= Field(default=None, description='员工ID')
    cate: int | None= Field(default=None, description='合同类别')
    cate_name: str | None = Field(None, description='合同类别名称')
    types: int | None= Field(default=None, description='合同类型')
    types_name: str | None = Field(None, description='合同类型名称')
    enterprise_id: int | None= Field(default=None, description='关联企业主体ID')
    enterprise_name: str | None = Field(None, description='企业名称')
    properties: int | None= Field(default=None, description='合同属性')
    properties_name: str | None = Field(None, description='合同属性名称')
    code: str = Field(default=None, description='合同编号')
    title: str = Field(default=None, description='合同名称')
    sign_time: int | str |None= Field(default=None, description='签订时间')
    start_time: int | str | None= Field(default=None, description='生效时间')
    end_time: int | str | None= Field(default=None, description='失效时间')
    secure_time: int | str | None= Field(default=None, description='解除时间')
    trial_months: int | None= Field(default=None, description='试用月数')
    trial_end_time: int | str | None= Field(default=None, description='试用结束时间')
    trial_salary: Decimal | str | None = Field(default=None, description='试用工资')
    worker_salary: Decimal | str | None = Field(default=None, description='转正工资')
    status: int | None= Field(default=None, description='合同状态')
    status_name: str | None = Field(None, description='合同状态名称')
    file_ids: str = Field(default=None, description='附件')
    file_ids_list: Optional[List[str]] = Field(None, description='附件列表')
    remark: str | None = Field(None, description='备注说明')
    admin_id: int | None= Field(default=None, description='创建人ID')
    create_time: int | None= Field(default=None, description='添加时间')
    update_time: int | None= Field(default=None, description='修改时间')
    delete_time: int | None= Field(default=None, description='删除时间')

    @field_serializer('sign_time')
    def serialize_sign_time(self, value: Optional[int]) -> Optional[str]:
        """序列化签订时间"""
        return format_timestamp(value)
    @field_serializer('start_time')
    def serialize_start_time(self, value: Optional[int]) -> Optional[str]:
        """序列化生效时间"""
        return format_timestamp(value)
    @field_serializer('end_time')
    def serialize_end_time(self, value: Optional[int]) -> Optional[str]:
        """序列化失效时间"""
        return format_timestamp(value)

    @field_serializer('trial_end_time')
    def serialize_trial_end_time(self, value: Optional[int]) -> Optional[str]:
        """序列化试用结束时间"""
        return format_timestamp(value)

    @field_serializer('secure_time')
    def serialize_secure_time(self, value: Optional[int]) -> Optional[str]:
        """序列化解除时间"""
        return format_timestamp(value)
    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)

    @field_serializer('delete_time')
    def serialize_delete_time(self, value: Optional[int]) -> Optional[str]:
        """序列化删除时间"""
        return format_timestamp(value)

class OaLaborContractQueryModel(OaLaborContractBaseModel):
    """奖罚记录 VO - 用于查询条件"""
    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')

class OaLaborContractPageQueryModel(OaLaborContractQueryModel):
    """奖罚记录分页查询VO"""
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')
