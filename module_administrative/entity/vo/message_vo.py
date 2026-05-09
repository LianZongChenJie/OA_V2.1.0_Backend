from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer, field_validator
from utils.timeformat import format_timestamp
from typing import Optional
from pydantic.alias_generators import to_camel


class OaMessageBaseModel(BaseModel):
    """消息基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    title: str | None = Field(None, description='消息主题')
    template: str | None = Field(None, description='消息模板')
    content: str | None = Field(None, description='消息内容')
    file_ids: str | None = Field(None, description='消息附件')
    from_uid: int | None = Field(None, description='发送人id，0为系统消息')
    types: int | None = Field(None, description='接收人类型：1人员,2部门,3岗位,4全部')
    uids: str | None = Field(None, description='人员ids，逗号分隔')
    dids: str | None = Field(None, description='部门ids，逗号分隔')
    pids: str | None = Field(None, description='岗位ids，逗号分隔')
    copy_uids: str | None = Field(None, description='抄送人员ids，逗号分隔')
    msg_id: int | None = Field(None, description='转发、回复关联消息id')
    is_draft: int | None = Field(None, description='是否是草稿：1正常消息 2草稿消息')
    send_time: int | None = Field(None, description='发送日期')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')
    delete_time: int | None = Field(None, description='删除时间')
    clear_time: int | None = Field(None, description='清除时间')
    action_id: int | None = Field(None, description='操作模块数据的id')

    @field_serializer('send_time')
    def serialize_send_time(self, value: Optional[int]) -> Optional[str]:
        """序列化发送时间"""
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

    @field_serializer('clear_time')
    def serialize_clear_time(self, value: Optional[int]) -> Optional[str]:
        """序列化清除时间"""
        return format_timestamp(value)

    @field_validator('types')
    def validate_types(cls, v):
        """验证接收人类型"""
        if v is not None and v not in [1, 2, 3, 4]:
            raise ValueError('接收人类型必须是1,2,3,4')
        return v

    @field_validator('is_draft')
    def validate_is_draft(cls, v):
        """验证草稿状态"""
        if v is not None and v not in [1, 2]:
            raise ValueError('草稿状态必须是1或2')
        return v


class OaMessageQueryModel(OaMessageBaseModel):
    """消息查询VO"""

    keyword: Optional[str] = Field(None, description='关键字（标题模糊查询）')
    begin_time: Optional[int] = Field(None, description='开始时间')
    end_time: Optional[int] = Field(None, description='结束时间')

class OaMessagePageQueryModel(OaMessageQueryModel):
    """
    分页查询VO
    """
    page_num: int = Field(default=1, description='页码')
    page_size: int = Field(default=20, description='每页条数')

class OaMessageDeleteModel(BaseModel):
    """
    消息删除VO
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    message_ids: list[int] = Field([], description='消息id集合')
    table: str = Field("", description='表名')

class OaMessageStarModel(BaseModel):
    """
    消息删除VO
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    message_ids: list[int] = Field([], description='消息id集合')
    is_star: int = Field(0, description='标星状态')

class OaMessageClearModel(BaseModel):
    """
    消息删除VO
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    message_id: int = Field(0, description='消息id集合')
    table: str = Field("", description='表名')

class OaMessageReadModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    message_id: int = Field(0, description='消息id')