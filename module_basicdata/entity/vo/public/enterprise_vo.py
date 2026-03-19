from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp
from typing import Optional


class OaEnterpriseBaseModel(BaseModel):
    """企业主体基础VO"""

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    title: str | None = Field(None, description='企业名称')
    city: str | None = Field(None, description='所在城市')
    bank: str | None = Field(None, description='开户银行')
    bank_sn: str | None = Field(None, description='银行帐号')
    tax_num: str | None = Field(None, description='纳税人识别号')
    phone: str | None = Field(None, description='开票电话')
    address: str | None = Field(None, description='开票地址')
    remark: str | None = Field(None, description='备注说明')
    status: int | None  = Field(None, description='状态：-1删除 0禁用 1启用')
    create_time: int | None  = Field(None, description='创建时间')
    update_time: int | None  = Field(None, description='更新时间')

    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        else:
            return v

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)


class OaEnterprisePageModel(OaEnterpriseBaseModel):
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='每页大小')
