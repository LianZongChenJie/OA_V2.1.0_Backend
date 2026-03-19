from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp
from typing import Optional


class OaBasicCustomerBaseModel(BaseModel):
    """客户常规数据基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: Optional[int] = Field(None, description='ID')
    types: Optional[str] = Field(None, description='数据类型:1客户状态,2客户意向,3跟进方式,4销售阶段')
    title: Optional[str] = Field(None, description='名称')
    status: Optional[int] = Field(None, description='状态：-1删除 0禁用 1启用')
    create_time: Optional[int] = Field(None, description='创建时间')
    update_time: Optional[int] = Field(None, description='更新时间')

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)


class OaBasicCustomerPageQueryModel(OaBasicCustomerBaseModel):
    """客户常规数据分页查询VO"""
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')