from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class CustomerChanceModel(BaseModel):
    """
    客户机会表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='机会 ID')
    title: str | None = Field(default=None, description='销售机会主题')
    cid: int | None = Field(default=None, description='客户 ID')
    contact_id: int | None = Field(default=None, description='联系人 ID')
    services_id: int | None = Field(default=None, description='需求服务 ID')
    stage: int | None = Field(default=None, description='当前阶段')
    content: str | None = Field(default=None, description='需求描述')
    discovery_time: int | None = Field(default=None, description='发现时间')
    expected_time: int | None = Field(default=None, description='预计签单时间')
    expected_amount: float | None = Field(default=None, description='预计签单金额')
    admin_id: int | None = Field(default=None, description='创建人')
    belong_uid: int | None = Field(default=None, description='所属人')
    assist_ids: str | None = Field(default=None, description='协助人员，如:1,2,3')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    @Xss(field_name='title', message='机会主题不能包含脚本字符')
    @NotBlank(field_name='title', message='机会主题不能为空')
    @Size(field_name='title', min_length=0, max_length=255, message='机会主题长度不能超过 255 个字符')
    def get_title(self) -> str | None:
        return self.title

    @Xss(field_name='content', message='需求描述不能包含脚本字符')
    @Size(field_name='content', min_length=0, max_length=16777215, message='需求描述长度超出限制')
    def get_content(self) -> str | None:
        return self.content

    def validate_fields(self) -> None:
        self.get_title()
        self.get_content()


class CustomerChanceTreeModel(CustomerChanceModel):
    """
    客户机会树模型
    """

    label: str | None = Field(default=None, description='机会名称（用于树显示）')
    parentId: int | None = Field(default=None, description='父分类 ID（用于构建树结构）')
    children: list['CustomerChanceTreeModel'] | None = Field(default=[], description='子机会')


class CustomerChanceQueryModel(CustomerChanceModel):
    """
    客户机会不分页查询模型
    """

    pass


class CustomerChancePageQueryModel(CustomerChanceQueryModel):
    """
    客户机会分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddCustomerChanceModel(CustomerChanceModel):
    """
    新增客户机会模型
    """

    pass


class EditCustomerChanceModel(AddCustomerChanceModel):
    """
    编辑客户机会模型
    """

    pass


class DeleteCustomerChanceModel(BaseModel):
    """
    删除客户机会模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的机会 ID')
