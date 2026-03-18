from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class PropertyBrandModel(BaseModel):
    """
    资产品牌表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='品牌 ID')
    title: str | None = Field(default=None, description='品牌名称')
    sort: int | None = Field(default=None, description='排序：越大越靠前')
    desc: str | None = Field(default=None, description='描述')
    status: Literal[-1, 0, 1] | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')

    @Xss(field_name='title', message='品牌名称不能包含脚本字符')
    @NotBlank(field_name='title', message='品牌名称不能为空')
    @Size(field_name='title', min_length=0, max_length=100, message='品牌名称长度不能超过 100 个字符')
    def get_title(self) -> str | None:
        return self.title

    @Xss(field_name='desc', message='描述不能包含脚本字符')
    @Size(field_name='desc', min_length=0, max_length=1000, message='描述长度不能超过 1000 个字符')
    def get_desc(self) -> str | None:
        return self.desc

    def validate_fields(self) -> None:
        self.get_title()
        self.get_desc()


class PropertyBrandQueryModel(PropertyBrandModel):
    """
    资产品牌不分页查询模型
    """

    pass


class PropertyBrandPageQueryModel(PropertyBrandQueryModel):
    """
    资产品牌分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddPropertyBrandModel(PropertyBrandModel):
    """
    新增资产品牌模型
    """

    pass


class EditPropertyBrandModel(AddPropertyBrandModel):
    """
    编辑资产品牌模型
    """

    pass


class DeletePropertyBrandModel(BaseModel):
    """
    删除资产品牌模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的品牌 ID')
