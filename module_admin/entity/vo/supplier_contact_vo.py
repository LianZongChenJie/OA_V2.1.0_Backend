from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class SupplierContactModel(BaseModel):
    """
    供应商联系人表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='联系人 ID')
    name: str | None = Field(default=None, description='联系人姓名')
    mobile: str | None = Field(default=None, description='联系电话')
    sex: str | None = Field(default=None, description='性别')
    sid: int | None = Field(default=None, description='供应商 ID')
    is_default: int | None = Field(default=None, description='是否默认联系人：0 否 1 是')
    admin_id: int | None = Field(default=None, description='创建人')
    status: Literal[-1, 0, 1] | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    @Xss(field_name='name', message='联系人姓名不能包含脚本字符')
    @NotBlank(field_name='name', message='联系人姓名不能为空')
    @Size(field_name='name', min_length=0, max_length=100, message='联系人姓名长度不能超过 100 个字符')
    def get_name(self) -> str | None:
        return self.name

    @NotBlank(field_name='mobile', message='联系电话不能为空')
    @Size(field_name='mobile', min_length=0, max_length=20, message='联系电话长度不能超过 20 个字符')
    def get_mobile(self) -> str | None:
        return self.mobile

    def validate_fields(self) -> None:
        self.get_name()
        self.get_mobile()


class SupplierContactPageQueryModel(SupplierContactModel):
    """
    供应商联系人分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddSupplierContactModel(SupplierContactModel):
    """
    新增供应商联系人模型
    """

    pass


class EditSupplierContactModel(AddSupplierContactModel):
    """
    编辑供应商联系人模型
    """

    pass


class DeleteSupplierContactModel(BaseModel):
    """
    删除供应商联系人模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的联系人 ID')
    type: int | None = Field(default=None, description='删除类型')
