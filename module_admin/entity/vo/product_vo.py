from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class ProductModel(BaseModel):
    """
    产品表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='产品 ID')
    title: str | None = Field(default=None, description='产品名称')
    cate_id: int | None = Field(default=None, description='产品分类 ID')
    thumb: int | None = Field(default=None, description='缩略图 ID')
    code: str | None = Field(default=None, description='产品编码')
    barcode: str | None = Field(default=None, description='条形码')
    unit: str | None = Field(default=None, description='单位')
    specs: str | None = Field(default=None, description='规格')
    brand: str | None = Field(default=None, description='品牌')
    producer: str | None = Field(default=None, description='生产商')
    base_price: Decimal | None = Field(default=None, description='成本价')
    purchase_price: Decimal | None = Field(default=None, description='采购价')
    sale_price: Decimal | None = Field(default=None, description='销售价')
    content: str | None = Field(default=None, description='产品描述')
    album_ids: str | None = Field(default=None, description='产品相册 ids')
    file_ids: str | None = Field(default=None, description='产品附件 ids')
    stock: int | None = Field(default=None, description='库存')
    is_object: Literal[1, 2] | None = Field(default=None, description='是否是实物，1 是 2 不是')
    status: Literal[0, 1] | None = Field(default=None, description='状态：0 禁用 1 启用')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    @Xss(field_name='title', message='产品名称不能包含脚本字符')
    @NotBlank(field_name='title', message='产品名称不能为空')
    @Size(field_name='title', min_length=0, max_length=100, message='产品名称长度不能超过 100 个字符')
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

    @Xss(field_name='unit', message='单位不能包含脚本字符')
    @Size(field_name='unit', min_length=0, max_length=100, message='单位长度不能超过 100 个字符')
    def get_unit(self) -> str | None:
        return self.unit

    @Xss(field_name='specs', message='规格不能包含脚本字符')
    @Size(field_name='specs', min_length=0, max_length=100, message='规格长度不能超过 100 个字符')
    def get_specs(self) -> str | None:
        return self.specs

    @Xss(field_name='brand', message='品牌不能包含脚本字符')
    @Size(field_name='brand', min_length=0, max_length=100, message='品牌长度不能超过 100 个字符')
    def get_brand(self) -> str | None:
        return self.brand

    @Xss(field_name='producer', message='生产商不能包含脚本字符')
    @Size(field_name='producer', min_length=0, max_length=100, message='生产商长度不能超过 100 个字符')
    def get_producer(self) -> str | None:
        return self.producer

    @field_validator('base_price', 'purchase_price', 'sale_price', mode='before')
    @classmethod
    def validate_price(cls, v):
        if v is None:
            return Decimal('0.00')
        return Decimal(str(v))

    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return None
        return int(v)

    def validate_fields(self) -> None:
        self.get_title()
        self.get_code()
        self.get_barcode()
        self.get_unit()
        self.get_specs()
        self.get_brand()
        self.get_producer()


class ProductPageQueryModel(ProductModel):
    """
    产品分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    cate_id: int | None = Field(default=None, description='分类 ID')


class AddProductModel(ProductModel):
    """
    新增产品模型
    """

    pass


class EditProductModel(AddProductModel):
    """
    编辑产品模型
    """

    pass


class DeleteProductModel(BaseModel):
    """
    删除产品模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的产品 ID')

