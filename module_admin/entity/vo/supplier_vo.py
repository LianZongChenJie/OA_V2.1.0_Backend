from typing import Literal
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss

from module_admin.entity.vo.supplier_contact_vo import AddSupplierContactModel, SupplierContactModel


class SupplierModel(BaseModel):
    """
    供应商表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='供应商 ID')
    title: str | None = Field(default=None, description='供应商名称')
    code: str | None = Field(default=None, description='供应商编号')
    phone: str | None = Field(default=None, description='供应商电话')
    email: str | None = Field(default=None, description='供应商邮箱')
    address: str | None = Field(default=None, description='供应商联系地址')
    file_ids: str | None = Field(default=None, description='附件 ids')
    products: str | None = Field(default=None, description='供应商商品')
    content: str | None = Field(default=None, description='供应商描述')
    status: Literal[-1, 0, 1] | None = Field(default=None, description='供应商状态：0 禁用，1 启用')
    tax_num: str | None = Field(default=None, description='纳税人识别号')
    tax_mobile: str | None = Field(default=None, description='开票电话')
    tax_address: str | None = Field(default=None, description='开票地址')
    tax_bank: str | None = Field(default=None, description='开户银行')
    tax_banksn: str | None = Field(default=None, description='银行帐号')
    file_license_ids: str | None = Field(default=None, description='营业执照附件')
    file_idcard_ids: str | None = Field(default=None, description='身份证附件')
    file_bankcard_ids: str | None = Field(default=None, description='银行卡附件')
    file_openbank_ids: str | None = Field(default=None, description='开户行附件')
    tax_rate: Decimal | None = Field(default=None, description='税率')
    admin_id: int | None = Field(default=None, description='录入人')
    sort: int | None = Field(default=None, description='排序')
    create_time: int | None = Field(default=None, description='添加时间')
    update_time: int | None = Field(default=None, description='修改时间')
    delete_time: int | None = Field(default=None, description='删除时间')
    
    # 扩展字段：联系人列表（仅用于详情返回）
    contact_list: list[SupplierContactModel] | None = Field(default=None, description='联系人列表')

    @Xss(field_name='title', message='供应商名称不能包含脚本字符')
    @NotBlank(field_name='title', message='供应商名称不能为空')
    @Size(field_name='title', min_length=0, max_length=255, message='供应商名称长度不能超过 255 个字符')
    def get_title(self) -> str | None:
        return self.title

    def validate_fields(self) -> None:
        self.get_title()


class SupplierPageQueryModel(SupplierModel):
    """
    供应商管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键字')


class AddSupplierModel(SupplierModel):
    """
    新增供应商模型
    """

    contact_list: list[AddSupplierContactModel] | None = Field(default=None, description='联系人列表')


class EditSupplierModel(AddSupplierModel):
    """
    编辑供应商模型
    """

    pass


class DeleteSupplierModel(BaseModel):
    """
    删除供应商模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的供应商 ID')
    type: int | None = Field(default=None, description='删除类型')
