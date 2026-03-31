from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

from utils.timeformat import format_timestamp
from typing import Optional


class OaNewsBaseModel(BaseModel):
    """新闻基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: Optional[int] = Field(None, description='ID')
    title: Optional[str] = Field(None, description='标题')
    content: Optional[str] = Field(None, description='新闻内容')
    src: Optional[str] = Field(None, description='关联链接')
    sort: Optional[int] = Field(None, description='排序')
    file_ids: Optional[str] = Field(None, description='相关附件')
    admin_id: Optional[int] = Field(None, description='发布人id')
    create_time: Optional[int] = Field(None, description='创建时间')
    update_time: Optional[int] = Field(None, description='更新时间')
    delete_time: Optional[int] = Field(None, description='删除时间')

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> str | None:
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
class OaNewsQueryPageModel(OaNewsBaseModel):
    """公司新闻查询VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    page_num: int | None = Field(1, description='页码')
    page_size: int | None = Field(20, description='页大小')
    keyword: str | None = Field(None, description='关键字')