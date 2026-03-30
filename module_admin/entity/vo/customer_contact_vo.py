from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class CustomerContactModel(BaseModel):
    """
    客户联系人表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='联系人 ID')
    cid: int | None = Field(default=None, description='客户 ID')
    is_default: int | None = Field(default=None, description='是否是第一联系人')
    name: str | None = Field(default=None, description='姓名')
    sex: Literal[0, 1, 2] | None = Field(default=None, description='用户性别:0 未知，1 男，2 女')
    mobile: str | None = Field(default=None, description='手机号码')
    qq: str | None = Field(default=None, description='QQ 号')
    wechat: str | None = Field(default=None, description='微信号')
    email: str | None = Field(default=None, description='邮件地址')
    nickname: str | None = Field(default=None, description='称谓')
    department: str | None = Field(default=None, description='部门')
    position: str | None = Field(default=None, description='职位')
    birthday: str | None = Field(default=None, description='生日')
    address: str | None = Field(default=None, description='家庭住址')
    family: str | None = Field(default=None, description='家庭成员')
    admin_id: int | None = Field(default=None, description='创建人')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    # 扩展字段，用于列表展示
    customer_name: str | None = Field(default=None, description='客户名称')

    @Xss(field_name='name', message='姓名不能包含脚本字符')
    @NotBlank(field_name='name', message='姓名不能为空')
    @Size(field_name='name', min_length=0, max_length=100, message='姓名长度不能超过 100 个字符')
    def get_name(self) -> str | None:
        return self.name

    @Xss(field_name='mobile', message='手机号码不能包含脚本字符')
    @Size(field_name='mobile', min_length=0, max_length=20, message='手机号码长度不能超过 20 个字符')
    def get_mobile(self) -> str | None:
        return self.mobile

    @Xss(field_name='email', message='邮箱地址不能包含脚本字符')
    @Size(field_name='email', min_length=0, max_length=100, message='邮箱地址长度不能超过 100 个字符')
    def get_email(self) -> str | None:
        return self.email

    def validate_fields(self) -> None:
        self.get_name()


class CustomerContactPageQueryModel(CustomerContactModel):
    """
    客户联系人分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    cid: int | None = Field(default=None, description='客户 ID')


class AddCustomerContactModel(CustomerContactModel):
    """
    新增客户联系人模型
    """

    pass


class EditCustomerContactModel(AddCustomerContactModel):
    """
    编辑客户联系人模型
    """

    pass


class DeleteCustomerContactModel(BaseModel):
    """
    删除客户联系人模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的联系人 ID')

