from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

from utils.timeformat import format_timestamp
from typing import Optional

class OaMsgBaseModel(BaseModel):
    """消息基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    id: int | None = Field(None, description='ID')
    title: str | None = Field(None, description='消息主题')
    template: str | None = Field(None, description='消息模板,默认是私人文本消息,其他则在配置文件查看消息模板')
    content: str | None = Field(None, description='消息内容')
    file_ids: str | None = Field(None, description='消息附件')
    from_uid: int | None = Field(None, description='发送人id，0为系统消息')
    to_uid: int | None = Field(None, description='接收人id')
    message_id: int | None = Field(None, description='来源发件消息id,0为系统消息')
    msg_id: int | None = Field(None, description='转发、回复关联消息id')
    is_star: int | None = Field(None, description='是否星标信息：1是 0不是')
    read_time: int | None = Field(None, description='阅读时间')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')
    delete_time: int | None = Field(None, description='删除时间')
    clear_time: int | None = Field(None, description='清除时间')
    action_id: int | None = Field(None, description='操作模块数据的id（针对系统消息）')

    @field_serializer('read_time')
    def serialize_read_time(self, value: Optional[int]) -> str | None:
        """序列化阅读时间"""
        return format_timestamp(value)

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

    @field_serializer('clear_time')
    def serialize_clear_time(self, value: Optional[int]) -> Optional[str]:
        """序列化清除时间"""
        return format_timestamp(value)

class OaMsgQueryPageModel(OaMsgBaseModel):
    """消息查询页面VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    keyword: str | None = Field(None, description='关键字')
    page_num: Optional[int] = Field(None, description='页码')
    page_size: Optional[int] = Field(None, description='每页条数')