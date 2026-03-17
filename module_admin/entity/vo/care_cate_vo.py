from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class CareCateModel(BaseModel):
    """
    关怀项目表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='关怀项目 ID')
    title: str | None = Field(default=None, description='关怀项目名称')
    status: Literal[-1, 0, 1] | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')

    @Xss(field_name='title', message='关怀项目名称不能包含脚本字符')
    @NotBlank(field_name='title', message='关怀项目名称不能为空')
    @Size(field_name='title', min_length=0, max_length=100, message='关怀项目名称长度不能超过 100 个字符')
    def get_title(self) -> str | None:
        return self.title

    def validate_fields(self) -> None:
        self.get_title()


class CareCatePageQueryModel(CareCateModel):
    """
    关怀项目管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddCareCateModel(CareCateModel):
    """
    新增关怀项目模型
    """

    pass


class EditCareCateModel(AddCareCateModel):
    """
    编辑关怀项目模型
    """

    pass


class DeleteCareCateModel(BaseModel):
    """
    删除关怀项目模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的关怀项目 ID')

