from typing import Literal, Any, Union
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss
from decimal import Decimal

class PropertyModel(BaseModel):
    """
    资产表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    title: str | None = Field(default=None, description='名称')
    code: str | None = Field(default=None, description='编号')
    thumb: int | None = Field(default=None, description='缩略图')
    cate_id: int | None = Field(default=None, description='资产分类id')
    brand_id: int | None = Field(default=None, description='品牌名称')
    unit_id: int | None = Field(default=None, description='单位')
    quality_time: Union[int, str, None] = Field(default=None, description='质保到期日期（支持时间戳或日期字符串）')
    buy_time: Union[int, str, None] = Field(default=None, description='购进日期（支持时间戳或日期字符串）')
    price: Decimal | None = Field(default=None, description='价格')
    rate: Decimal | None = Field(default=None, description='年折旧率')
    model_: str | None = Field(default=None, description='规格型号')
    address: str | None = Field(default=None, description='所放位置')
    user_dids: str | None = Field(default=None, description='使用部门')
    user_ids: str | None = Field(default=None, description='使用人员')
    content: str | None = Field(default=None, description='资产描述')
    file_ids: str | None = Field(default=None, description='资产附件ids,如:1,2,3')
    source: Literal[1, 2, 3, 4] | None = Field(default=None, description='来源：1采购,2赠与,3自产,4其他')
    purchase_id: int | None = Field(default=None, description='采购单ID')
    status: Literal[-1, 0, 1, 2, 3, 4] | None = Field(default=None, description='状态：-1删除 0闲置,1在用,2维修,3报废,4丢失')
    admin_id: int | None = Field(default=None, description='创建人')
    create_time: Union[int, str, None] = Field(default=None, description='创建时间')
    update_id: int | None = Field(default=None, description='编辑人')
    update_time: Union[int, str, None] = Field(default=None, description='更新时间')
    
    # 扩展字段：关联查询结果
    cate_name: str | None = Field(default=None, description='资产分类名称')
    brand_name: str | None = Field(default=None, description='品牌名称')
    unit_name: str | None = Field(default=None, description='计量单位名称')
    admin_name: str | None = Field(default=None, description='创建人姓名')
    update_name: str | None = Field(default=None, description='最后修改人姓名')

    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """将字符串类型的 status 转换为整数"""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return v

    @field_validator('source', mode='before')
    @classmethod
    def validate_source(cls, v):
        """将字符串类型的 source 转换为整数"""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return v

    @field_validator('create_time', mode='before')
    @classmethod
    def validate_create_time(cls, v):
        """处理 create_time 字段，支持时间戳整数或日期字符串"""
        if v is None or v == '':
            return None
        return v

    @field_validator('update_time', mode='before')
    @classmethod
    def validate_update_time(cls, v):
        """处理 update_time 字段，支持时间戳整数或日期字符串"""
        if v is None or v == '':
            return None
        return v

    @Xss(field_name='title', message='名称不能包含脚本字符')
    @NotBlank(field_name='title', message='名称不能为空')
    @Size(field_name='title', min_length=0, max_length=100, message='名称长度不能超过 100 个字符')
    def get_title(self) -> str | None:
        return self.title

    @Xss(field_name='code', message='编号不能包含脚本字符')
    @Size(field_name='code', min_length=0, max_length=100, message='编号长度不能超过 100 个字符')
    def get_code(self) -> str | None:
        return self.code

    @Xss(field_name='model_', message='规格型号不能包含脚本字符')
    @Size(field_name='model_', min_length=0, max_length=255, message='规格型号长度不能超过 255 个字符')
    def get_model_(self) -> str | None:
        return self.model_

    @Xss(field_name='address', message='所放位置不能包含脚本字符')
    @Size(field_name='address', min_length=0, max_length=255, message='所放位置长度不能超过 255 个字符')
    def get_address(self) -> str | None:
        return self.address

    @Xss(field_name='content', message='资产描述不能包含脚本字符')
    @Size(field_name='content', min_length=0, max_length=65535, message='资产描述长度不能超过 65535 个字符')
    def get_content(self) -> str | None:
        return self.content

    def validate_fields(self) -> None:
        self.get_title()
        self.get_code()
        self.get_model_()
        self.get_address()
        self.get_content()

class PropertyQueryModel(PropertyModel):
    """
    资产不分页查询模型
    """
    pass

class PropertyPageQueryModel(PropertyQueryModel):
    """
    资产分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')

class AddPropertyModel(PropertyModel):
    """
    新增资产模型
    """
    pass

class EditPropertyModel(AddPropertyModel):
    """
    编辑资产模型
    """
    pass

class DeletePropertyModel(BaseModel):
    """
    删除资产模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的资产 ID')