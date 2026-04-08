from typing import Literal
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class PurchasedModel(BaseModel):
    """
    采购品表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='采购品 ID')
    title: str | None = Field(default=None, description='采购品名称')
    cate_id: int | None = Field(default=None, description='采购分类 id')
    cate_name: str | None = Field(default=None, description='采购分类名称')
    thumb: int | None = Field(default=None, description='缩略图 id')
    code: str | None = Field(default=None, description='产品编码')
    barcode: str | None = Field(default=None, description='条形码')
    unit: str | None = Field(default=None, description='单位')
    specs: str | None = Field(default=None, description='规格')
    brand: str | None = Field(default=None, description='品牌')
    producer: str | None = Field(default=None, description='生产商')
    purchase_price: Decimal | None = Field(default=None, description='采购价')
    sale_price: Decimal | None = Field(default=None, description='销售价')
    content: str | None = Field(default=None, description='商品描述')
    album_ids: str | None = Field(default=None, description='采购品相册 ids')
    file_ids: str | None = Field(default=None, description='采购品附件 ids')
    stock: int | None = Field(default=None, description='库存')
    is_object: int | None = Field(default=None, description='是否是实物，1 是 2 不是')
    status: int | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    @Xss(field_name='title', message='采购品名称不能包含脚本字符')
    @NotBlank(field_name='title', message='采购品名称不能为空')
    @Size(field_name='title', min_length=0, max_length=100, message='采购品名称长度不能超过 100 个字符')
    def get_title(self) -> str | None:
        return self.title

    @Xss(field_name='code', message='产品编码不能包含脚本字符')
    @Size(field_name='code', min_length=0, max_length=255, message='产品编码长度不能超过 255 个字符')
    def get_code(self) -> str | None:
        return self.code

    @Xss(field_name='barcode', message='条形码不能包含脚本字符')
    @Size(field_name='barcode', min_length=0, max_length=255, message='条形码长度不能超过 255 个字符')
    def get_barcode(self) -> str | None:
        return self.barcode

    def validate_fields(self) -> None:
        self.get_title()
        self.get_code()
        self.get_barcode()


class PurchasedPageQueryModel(PurchasedModel):
    """
    采购品分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键字')
    status: int | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')


class AddPurchasedModel(PurchasedModel):
    """
    新增采购品模型
    """

    pass


class EditPurchasedModel(AddPurchasedModel):
    """
    编辑采购品模型
    """

    pass


class DeletePurchasedModel(BaseModel):
    """
    删除采购品模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的采购品 ID')
    type: int | None = Field(default=None, description='删除类型')
