from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from typing import Optional

from utils.timeformat import format_timestamp


class OaLinksBaseModel(BaseModel):
    """办公工具基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    title: str | None = Field(None, description='小工具名称')
    logo: int | None = Field(None, description='logo')
    url: str | None = Field(None, description='链接')
    target: int | None = Field(None, description='是否新窗口打开，1是,0否')
    sort: int | None = Field(None, description='排序')
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
        return format_timestamp(value) if value else None
class OaLinksPageQueryModel(OaLinksBaseModel):
    """办公工具分页查询VO"""
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')

