from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

from utils.timeformat import format_timestamp
from typing import Optional

class OaPlanBaseModel(BaseModel):
    """日程安排基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None= Field(None, description='ID')
    title:str | None = Field(None, description='工作安排主题')
    type:str | None = Field(None, description='日程优先级')
    cid: int | None = Field(None, description='关联工作内容类型ID')
    cmid: int | None = Field(None, description='关联客户ID')
    ptid: int | None = Field(None, description='关联项目ID')
    admin_id: int | None = Field(None, description='关联创建员工ID')
    did: int | None = Field(None, description='所属部门')
    start_time: int | str | None = Field(None, description='开始时间')
    end_time: int | str | None = Field(None, description='结束时间')
    remind_type: int | None = Field(None, description='提醒类型')
    remind_time: int | None = Field(None, description='提醒时间')
    remark:str | None = Field(None, description='描述')
    file_ids:str | None = Field(None, description='相关附件')
    delete_time: int | None = Field(None, description='删除时间')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')

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

class OaPlanQueryModel(OaPlanBaseModel):
    """日程安排查询VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    before_time: int|None = Field(None, description='提前提醒时间')
    begin_time: str|None = Field(None, description='查询开始日期')
    end_time: str|None  = Field(None, description='查询结束日期')
    page_num: int | None = Field(1, description='页码')
    page_size: int | None = Field(20, description='页面数据量')

class OaPlanCalendarModel(BaseModel):
    """日程安排日历VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    backgroundColor: str | None = Field(None, description='背景色')
    borderColor: str | None = Field(None, description='边框色')
    end: str | None = Field(None, description='结束时间')
    start: str | None = Field(None, description='开始时间')
    id: int | None = Field(None, description='ID')
    remindType: int | None = Field(None, description='提醒类型')
    title: str | None = Field(None, description='标题')
    type: str | None = Field(None, description='优先级')
