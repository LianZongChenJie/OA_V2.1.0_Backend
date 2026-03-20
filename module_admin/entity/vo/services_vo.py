from typing import Literal
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class ServicesModel(BaseModel):
    """
    服务表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='服务 ID')
    title: str | None = Field(default=None, description='服务名称')
    cate_id: int | None = Field(default=None, description='服务分类 id')
    price: Decimal | None = Field(default=None, description='服务费用')
    content: str | None = Field(default=None, description='服务描述')
    sort: int | None = Field(default=None, description='排序')
    status: Literal[-1, 0, 1] | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    @Xss(field_name='title', message='服务名称不能包含脚本字符')
    @NotBlank(field_name='title', message='服务名称不能为空')
    @Size(field_name='title', min_length=0, max_length=100, message='服务名称长度不能超过 100 个字符')
    def get_title(self) -> str | None:
        return self.title

    def validate_fields(self) -> None:
        self.get_title()


class ServicesPageQueryModel(ServicesModel):
    """
    服务管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddServicesModel(ServicesModel):
    """
    新增服务模型
    """

    pass


class EditServicesModel(AddServicesModel):
    """
    编辑服务模型
    """

    pass


class DeleteServicesModel(BaseModel):
    """
    删除服务模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的服务 ID')
    type: int | None = Field(default=None, description='删除类型')
