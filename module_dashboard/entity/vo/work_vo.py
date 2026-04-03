from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp, int_time

class OaWorkBaseModel(BaseModel):
    """汇报工作基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    
    id: int  | None = Field(None, description='ID')
    types: int  | None = Field(None, description='类型：1 日报 2周报 3月报')
    start_date: int | str | None = Field(None, description='开始日期')
    end_date: int | str | None = Field(None, description='结束日期')
    to_uids: str  | None = Field(None, description='接受人员ID')
    works: str  | None = Field(None, description='汇报工作内容')
    plans: str  | None = Field(None, description='计划工作内容')
    remark: str  | None = Field(None, description='其他事项')
    file_ids: str  | None = Field(None, description='附件，如:1,2,3')
    send_time: int  | None = Field(None, description='发送时间')
    admin_id: int  | None = Field(None, description='创建人id')
    create_time: int  | None = Field(None, description='创建时间')
    update_time: int  | None = Field(None, description='更新时间')
    delete_time: int  | None = Field(None, description='删除时间')
    @validator('*', pre=True)
    def empty_string_to_none(cls, v):
        if isinstance(v, str) and len(v.strip()) == 0:
            return None
        return v

    @field_serializer('start_date')
    def serialize_start_date(self, value: str) -> int:
        """序列化开始日期"""
        return int_time(value)

    @field_serializer('end_date')
    def serialize_end_date(self, value: str) -> int:
        """序列化结束日期"""
        return int_time(value)

    @field_serializer('send_time')
    def serialize_send_time(self, value: int) -> str:
        """序列化发送时间"""
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
class OaWorkQueryModel(OaWorkBaseModel):
    """汇报工作查询VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    begin_time: str | None = Field(None, description='开始时间')
    end_time: str | None = Field(None, description='结束时间')
    keywork: str | None = Field(None, description='关键字')
    is_send: bool | None = Field(None, description='是否发送')

class OaWorkPageQueryModel(OaWorkQueryModel):
    """汇报工作分页查询VO"""
    page_num: int  = Field(default=1, ge=1, description='当前页码')
    page_size: int  = Field(default=10, ge=1, le=100, description='每页数量')
