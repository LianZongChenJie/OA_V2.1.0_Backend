from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel
from module_admin.entity.vo.user_vo import UserModel
from module_personnel.entity.vo.file_vo import OaFileBaseModel
from utils.timeformat import format_timestamp
from pydantic import field_serializer
from typing import Optional

class OaAdminProfilesBaseModel(BaseModel):
    """员工档案基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    admin_id: int | None = Field(None, description='员工ID')
    types: int | None = Field(None, description='类型:1教育经历/2工作经历/3相关证书/4计算机技能/5语言能力')
    title: str | None = Field(None, description='院校/公司/证书/技能/语言名称')
    start_time: str | None = Field(None, description='开始时间')
    end_time: str | None = Field(None, description='结束时间')
    speciality: str | None = Field(None, description='所学专业')
    education: str | None = Field(None, description='所获学历')
    authority: str | None = Field(None, description='颁发机构')
    position: str | None = Field(None, description='职位')
    know: int | None = Field(None, description='熟悉程度')
    remark: str | None = Field(None, description='备注说明')
    sort: int | None = Field(None, description='排序')
    create_time: int | None = Field(None, description='添加时间')
    update_time: int | None = Field(None, description='修改时间')
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

class OaAdminProfilesUpdateModel(BaseModel):
    profiles: list[OaAdminProfilesBaseModel] | None = Field(None, description='员工档案')
    user: UserModel | None = Field(default=None, description='员工信息')
    files: list[OaFileBaseModel] | None = Field(default=None, description='文件信息')
