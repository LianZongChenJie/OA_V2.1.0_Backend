# module_personnel/entity/vo/social_security_vo.py
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, List
from utils.timeformat import format_timestamp
from pydantic import field_serializer, field_validator


class OaSocialSecurityBaseModel(BaseModel):
    """社保信息基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: Optional[int] = Field(default=None, description='主键ID')
    city: Optional[str] = Field(default=None, description='所在城市')
    city_id: Optional[str] = Field(default=None, description='城市ID(多ID逗号分隔)')
    project_name: Optional[str] = Field(default=None, description='项目名称')
    remark: Optional[str] = Field(default=None, description='备注')
    social_date: Optional[int] = Field(default=15, description='社保日期(每月几号，1-31)')
    social_date_str: Optional[str] = Field(default=None, description='社保日期字符串')
    related_users: Optional[str] = Field(default=None, description='相关人员(逗号隔开)')
    # 创建人信息
    create_by: Optional[str] = Field(default=None, description='创建人')
    create_by_id: Optional[int] = Field(default=None, description='创建人ID')
    # 负责人信息
    manager: Optional[str] = Field(default=None, description='负责人')
    manager_id: Optional[int] = Field(default=None, description='负责人ID')
    status: Optional[int] = Field(default=1, description='状态：1正常，0终止')
    create_time: Optional[int] = Field(default=None, description='创建时间')
    create_time_str: Optional[str] = Field(default=None, description='创建时间字符串')
    update_time: Optional[int] = Field(default=None, description='更新时间')
    delete_time: Optional[int] = Field(default=None, description='删除时间')

    @field_validator('social_date', mode='before')
    @classmethod
    def validate_social_date(cls, v):
        """验证社保日期（每月几号，1-31）"""
        if v is None:
            return 15
        if isinstance(v, str):
            # 如果是字符串，尝试转换为整数
            try:
                v = int(v)
            except ValueError:
                # 字符串无法转换为整数，使用默认值
                return 15
        if isinstance(v, int):
            # 检查是否在有效范围内（1-31）
            if 1 <= v <= 31:
                return v
            # 如果超出范围（例如存储了时间戳），使用默认值
            return 15
        # 其他类型使用默认值
        return 15

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value) if value else None

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value) if value else None


class OaSocialSecurityPageQueryModel(OaSocialSecurityBaseModel):
    """社保信息分页查询VO"""
    page_num: Optional[int] = Field(default=1, description='页码')
    page_size: Optional[int] = Field(default=10, description='页大小')
    keywords: Optional[str] = Field(default=None, description='关键词搜索')
    status: Optional[int] = Field(default=None, description='状态筛选')


class OaSocialSecurityUserBaseModel(BaseModel):
    """社保关联人员基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: Optional[int] = Field(default=None, description='主键ID')
    social_id: Optional[int] = Field(default=None, description='社保信息ID')
    user_id: Optional[int] = Field(default=None, description='员工ID')
    user_name: Optional[str] = Field(default=None, description='员工名称')
    entry_time: Optional[int] = Field(default=None, description='入职时间')
    entry_time_str: Optional[str] = Field(default=None, description='入职时间字符串')
    department_name: Optional[str] = Field(default=None, description='归属部门')
    city: Optional[str] = Field(default=None, description='所在城市')
    project_name: Optional[str] = Field(default=None, description='项目名称')
    status: Optional[int] = Field(default=1, description='状态：1参保，0减员')
    create_time: Optional[int] = Field(default=None, description='创建时间')
    update_time: Optional[int] = Field(default=None, description='更新时间')
    delete_time: Optional[int] = Field(default=None, description='删除时间')

    @field_serializer('entry_time')
    def serialize_entry_time(self, value: Optional[int]) -> Optional[str]:
        """序列化入职时间"""
        return format_timestamp(value) if value else None

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value) if value else None


class OaSocialSecurityUserPageQueryModel(OaSocialSecurityUserBaseModel):
    """社保关联人员分页查询VO"""
    page_num: Optional[int] = Field(default=1, description='页码')
    page_size: Optional[int] = Field(default=10, description='页大小')
    social_id: Optional[int] = Field(default=None, description='社保信息ID')


class SocialSecurityWithUsersModel(BaseModel):
    """带关联人员的社保信息模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    social_info: OaSocialSecurityBaseModel = Field(..., description='社保信息')
    users: List[OaSocialSecurityUserBaseModel] = Field(default=[], description='关联人员列表')