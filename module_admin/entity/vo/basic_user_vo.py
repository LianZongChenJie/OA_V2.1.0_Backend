from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class BasicUserModel(BaseModel):
    """
    人事模块常规数据表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    types: str | None = Field(default=None, description='数据类型:1 职务，2 职级，3 看后期增加')
    title: str | None = Field(default=None, description='名称')
    status: Literal[-1, 0, 1] | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')

    @Xss(field_name='types', message='数据类型不能包含脚本字符')
    @NotBlank(field_name='types', message='数据类型不能为空')
    @Size(field_name='types', min_length=0, max_length=100, message='数据类型长度不能超过 100 个字符')
    def get_types(self) -> str | None:
        return self.types

    @Xss(field_name='title', message='名称不能包含脚本字符')
    @NotBlank(field_name='title', message='名称不能为空')
    @Size(field_name='title', min_length=0, max_length=100, message='名称长度不能超过 100 个字符')
    def get_title(self) -> str | None:
        return self.title

    def validate_fields(self) -> None:
        self.get_types()
        self.get_title()


class BasicUserQueryModel(BasicUserModel):
    """
    人事模块常规数据不分页查询模型
    """

    pass


class BasicUserPageQueryModel(BasicUserQueryModel):
    """
    人事模块常规数据分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddBasicUserModel(BasicUserModel):
    """
    新增人事模块常规数据模型
    """

    pass


class EditBasicUserModel(AddBasicUserModel):
    """
    编辑人事模块常规数据模型
    """

    pass


class DeleteBasicUserModel(BaseModel):
    """
    删除人事模块常规数据模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的数据 ID')

