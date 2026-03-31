from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

from utils.timeformat import format_timestamp
from typing import Optional

class OaPlanVO(BaseModel):
    """日程安排基础VO"""

    id: Optional[int] = Field(None, description='ID')
    title: Optional[str] = Field(None, description='工作安排主题')
    type: Optional[str] = Field(None, description='日程优先级')
    cid: Optional[int] = Field(None, description='关联工作内容类型ID')
    cmid: Optional[int] = Field(None, description='关联客户ID')
    ptid: Optional[int] = Field(None, description='关联项目ID')
    admin_id: Optional[int] = Field(None, description='关联创建员工ID')
    did: Optional[int] = Field(None, description='所属部门')
    start_time: Optional[int] = Field(None, description='开始时间')
    end_time: Optional[int] = Field(None, description='结束时间')
    remind_type: Optional[int] = Field(None, description='提醒类型')
    remind_time: Optional[int] = Field(None, description='提醒时间')
    remark: Optional[str] = Field(None, description='描述')
    file_ids: Optional[str] = Field(None, description='相关附件')
    delete_time: Optional[int] = Field(None, description='删除时间')
    create_time: Optional[int] = Field(None, description='创建时间')
    update_time: Optional[int] = Field(None, description='更新时间')

    @validator("start_time", "end_time")
    def validate_datetime(cls, v):
        if not isinstance(v, int):
            raise ValueError("必须是整数")
        return v

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
