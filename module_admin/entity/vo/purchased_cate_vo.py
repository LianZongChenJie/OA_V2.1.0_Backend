from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class PurchasedCateModel(BaseModel):
    """
    采购品分类表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='分类 ID')
    title: str | None = Field(default=None, description='分类名称')
    pid: int | None = Field(default=None, description='父级分类 ID')
    sort: int | None = Field(default=None, description='排序：越大越靠前')
    desc: str | None = Field(default=None, description='分类说明')
    status: Literal[-1, 0, 1] | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')
    admin_id: int | None = Field(default=None, description='创建人')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')

    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """验证 status 字段的值，支持字符串转整数"""
        if v is None:
            return v
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                raise ValueError('status 必须是 -1、0 或 1')
        if v not in [-1, 0, 1]:
            raise ValueError('status 必须是 -1、0 或 1')
        return v

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


class PurchasedCateTreeModel(PurchasedCateModel):
    """
    采购品分类树模型
    """

    label: str | None = Field(default=None, description='分类名称（用于树显示）')
    children: list['PurchasedCateTreeModel'] | None = Field(default=[], description='子分类')


class PurchasedCatePageQueryModel(PurchasedCateModel):
    """
    采购品分类分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class PurchasedCateTreeQueryModel(BaseModel):
    """
    采购品分类树查询模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    pid: int | None = Field(default=None, description='父级分类 ID，用于获取指定父级下的子树')


class AddPurchasedCateModel(PurchasedCateModel):
    """
    新增采购品分类模型
    """

    pass


class EditPurchasedCateModel(AddPurchasedCateModel):
    """
    编辑采购品分类模型
    """

    pass


class DeletePurchasedCateModel(BaseModel):
    """
    删除采购品分类模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的分类 ID')
