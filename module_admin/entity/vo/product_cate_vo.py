from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class ProductCateModel(BaseModel):
    """
    产品分类表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='分类 ID')
    title: str | None = Field(default=None, description='分类名称')
    pid: int | None = Field(default=None, description='父分类 ID')
    sort: int | None = Field(default=None, description='排序：越大越靠前')
    desc: str | None = Field(default=None, description='分类说明')
    status: Literal[-1, 0, 1] | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')
    admin_id: int | None = Field(default=None, description='创建人')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')

    @Xss(field_name='title', message='分类名称不能包含脚本字符')
    @NotBlank(field_name='title', message='分类名称不能为空')
    @Size(field_name='title', min_length=0, max_length=100, message='分类名称长度不能超过 100 个字符')
    def get_title(self) -> str | None:
        return self.title

    @Xss(field_name='desc', message='分类说明不能包含脚本字符')
    @Size(field_name='desc', min_length=0, max_length=1000, message='分类说明长度不能超过 1000 个字符')
    def get_desc(self) -> str | None:
        return self.desc

    def validate_fields(self) -> None:
        self.get_title()
        self.get_desc()


class ProductCateTreeModel(ProductCateModel):
    """
    产品分类树模型
    """

    label: str | None = Field(default=None, description='分类名称（用于树显示）')
    parentId: int | None = Field(default=None, description='父分类 ID（用于构建树结构）')
    children: list['ProductCateTreeModel'] | None = Field(default=[], description='子分类')


class ProductCateQueryModel(ProductCateModel):
    """
    产品分类不分页查询模型
    """

    pass


class ProductCatePageQueryModel(ProductCateQueryModel):
    """
    产品分类分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddProductCateModel(ProductCateModel):
    """
    新增产品分类模型
    """

    pass


class EditProductCateModel(AddProductCateModel):
    """
    编辑产品分类模型
    """

    pass


class DeleteProductCateModel(BaseModel):
    """
    删除产品分类模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的分类 ID')

