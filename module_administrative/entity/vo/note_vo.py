from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

from utils.timeformat import format_timestamp
from typing import Optional


class OaNoteBaseModel(BaseModel):
    """公告基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    id: int | None = Field(None, description='ID')
    cate_id: int | None = Field(None, description='公告分类ID')
    sourse: int | None = Field(None, description='发布平台:1PC,2手机')
    title: str | None = Field(None, description='标题')
    content: str | None = Field(None, description='公告内容')
    src: str | None = Field(None, description='关联链接')
    status: int | None = Field(None, description='1可用-1禁用')
    sort: int | None = Field(None, description='排序')
    file_ids: str | None = Field(None, description='相关附件')
    role_type: int | None = Field(None, description='查看权限，0所有人,1部门,2人员')
    role_dids: str | None = Field(None, description='可查看部门')
    role_uids: str | None = Field(None, description='可查看用户')
    start_time: int | None = Field(None, description='展示开始时间')
    end_time: int | None = Field(None, description='展示结束时间')
    admin_id: int | None = Field(None, description='发布人id')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')
    delete_time: int | None = Field(None, description='删除时间')

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

class OaNoteQueryPageModel(OaNoteBaseModel):
    """公告查询页面VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    keyword: str | None = Field(None, description='关键字')
    page_num: Optional[int] = Field(None, description='页码')
    page_size: Optional[int] = Field(None, description='每页条数')