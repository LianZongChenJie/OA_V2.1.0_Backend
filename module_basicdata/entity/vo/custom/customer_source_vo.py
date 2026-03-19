from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp
from typing import Optional


class OaCustomerSourceBaseModel(BaseModel):
    """客户来源基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int | None = Field(None, description='ID')
    title: str | None = Field(None, description='客户渠道名称')
    sort: int | None = Field(None, description='排序，越大越靠前')
    status: int | None = Field(None, description='状态：0禁用 1启用')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')
    delete_time: int | None = Field(None, description='删除时间')

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

class OaCustomerSourcePageQueryModel(OaCustomerSourceBaseModel):
    """客户来源分页查询VO"""
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')