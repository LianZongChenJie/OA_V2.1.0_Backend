from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp
from pydantic import field_serializer
from typing import Optional
class OaFileBaseModel(BaseModel):
    """文件基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    module: str | None = Field(None, description='所属模块')
    sha1: str | None = Field(None, description='sha1')
    md5: str | None = Field(None, description='md5')
    name: str | None = Field(None, description='原始文件名')
    filename: str | None = Field(None, description='文件名')
    filepath: str | None = Field(None, description='文件路径+文件名')
    thumbpath: str | None = Field(None, description='缩略图路径')
    filesize: int | None = Field(None, description='文件大小')
    fileext: str | None = Field(None, description='文件后缀')
    mimetype: str | None = Field(None, description='文件类型')
    group_id: int | None = Field(None, description='文件分组ID')
    user_id: int | None = Field(None, description='上传会员ID')
    admin_id: int | None = Field(None, description='审核者id')
    status: int | None = Field(None, description='0未审核1已审核-1不通过')
    download: int | None = Field(None, description='下载量')
    uploadip: str | None = Field(None, description='上传IP')
    action: str | None = Field(None, description='来源模块功能')
    use: str | None = Field(None, description='用处')
    create_time: int | None = Field(None, description='创建时间')
    delete_time: int | None = Field(None, description='删除时间')
    audit_time: int | None = Field(None, description='审核时间')

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('audit_time')
    def serialize_audit_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)

    @field_serializer('delete_time')
    def serialize_delete_time(self, value: Optional[int]) -> Optional[str]:
        """序列化删除时间"""
        return format_timestamp(value)

