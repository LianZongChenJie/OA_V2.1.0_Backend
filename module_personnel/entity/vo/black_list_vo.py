from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp
from pydantic import field_serializer
from typing import Optional

class OaBlacklistBaseModel(BaseModel):
    """黑名单 VO - 用于数据展示"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    id: int | None= Field(default=None, description='主键ID')
    name:str | None= Field(default=None, description='姓名')
    mobile:str | None= Field(default=None, description='手机号码')
    idcard:str | None= Field(default=None, description='身份证')
    remark: str | None = Field(None, description='备注信息')
    admin_id: int | None= Field(default=None, description='创建人')
    admin_name: str | None = Field(None, description='创建人姓名')
    create_time: int | None= Field(default=None, description='申请时间')
    update_time: int | None= Field(default=None, description='更新信息时间')


    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)

class OaBlacklistPageQueryModel(OaBlacklistBaseModel):
    """黑名单分页查询VO"""
    keyword: str | None = Field(None, description='关键词')
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')
    