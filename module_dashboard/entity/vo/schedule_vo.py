from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from decimal import Decimal
from utils.timeformat import format_timestamp
from typing import Optional


class OaScheduleBaseModel(BaseModel):
    """工作记录基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    id: int | None = Field(None, description='ID')
    title: str | None = Field(None, description='工作记录主题')
    cid: int | None = Field(None, description='关联工作内容类型ID')
    cmid: int | None = Field(None, description='关联客户ID')
    ptid: int | None = Field(None, description='关联项目ID')
    tid: int | None = Field(None, description='关联任务ID')
    admin_id: int | None = Field(None, description='关联创建员工ID')
    did: int | None = Field(None, description='所属部门')
    start_time: int | str | None = Field(None, description='开始时间')
    end_time: int | str | None = Field(None, description='结束时间')
    labor_time: Decimal | None = Field(None, description='工时')
    labor_type: int | None = Field(None, description='工作类型:1案头2外勤')
    remark: str | None = Field(None, description='描述')
    file_ids: str | None = Field(None, description='相关附件')
    delete_time: int | None = Field(None, description='删除时间')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')



    @field_serializer('start_time')
    def serialize_start_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)

    @field_serializer('end_time')
    def serialize_end_time(self, value: Optional[int]) -> Optional[str]:
        """序列化删除时间"""
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



class OaScheduleQueryModel(OaScheduleBaseModel):
    """工作记录查询VO"""

    begin_time: str | None = Field(None, description='开始时间')
    end_time: str | None = Field(None, description='结束时间')
    range_time: str | None = Field(None, description='时间范围（格式：开始时间 至 结束时间）')
    keywords: str | None = Field(None, description='搜索关键词')
    uid: int | None = Field(None, description='用户ID筛选')

class OaSchedulePageQueryModel(OaScheduleQueryModel):
    """工作计划分页查询VO"""
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')

# class OaScheduleDetailModel(OaScheduleBaseModel):
#     """工作记录详情VO"""
#     model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
#     dept: SysDept | None = Field(default=None , description='所属部门详情')
#     user: SysUser | None = Field(default=None , description='关联创建员工详情')
#     cate: OaWorkCate | None = Field(default=None , description='关联工作内容类型详情')
