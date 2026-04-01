from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class CustomerTraceModel(BaseModel):
    """
    客户跟进记录表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, alias='id', description='跟进记录 ID')
    cid: int | None = Field(default=None, alias='cid', description='客户 ID')
    contact_id: int | None = Field(default=None, alias='contact_id', description='联系人 id')
    chance_id: int | None = Field(default=None, alias='chance_id', description='销售机会 id')
    types: int | None = Field(default=None, alias='types', description='跟进方式')
    stage: int | None = Field(default=None, alias='stage', description='当前阶段')
    content: str | None = Field(default=None, alias='content', description='跟进内容')
    follow_time: int | None = Field(default=None, alias='follow_time', description='跟进时间')
    next_time: int | None = Field(default=None, alias='next_time', description='下次跟进时间')
    file_ids: str | None = Field(default=None, alias='file_ids', description='附件 ids，如:1,2,3')
    admin_id: int | None = Field(default=None, alias='admin_id', description='创建人')
    create_time: int | None = Field(default=None, alias='create_time', description='创建时间')
    update_time: int | None = Field(default=None, alias='update_time', description='更新时间')
    delete_time: int | None = Field(default=None, alias='delete_time', description='删除时间')

    # 扩展字段，用于列表展示
    customer_name: str | None = Field(default=None, description='客户名称')
    contact_name: str | None = Field(default=None, description='联系人姓名')
    chance_title: str | None = Field(default=None, description='销售机会主题')
    types_name: str | None = Field(default=None, description='跟进方式名称')
    stage_name: str | None = Field(default=None, description='当前阶段名称')
    admin_name: str | None = Field(default=None, description='创建人姓名')
    follow_time_str: str | None = Field(default=None, description='跟进时间字符串')
    next_time_str: str | None = Field(default=None, description='下次跟进时间字符串')

    @Xss(field_name='content', message='跟进内容不能包含脚本字符')
    @Size(field_name='content', min_length=0, max_length=16777215, message='跟进内容长度超出限制')
    def get_content(self) -> str | None:
        return self.content

    def validate_fields(self) -> None:
        self.get_content()


class CustomerTracePageQueryModel(CustomerTraceModel):
    """
    客户跟进记录分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    follow_time_start: int | None = Field(default=None, description='跟进开始时间')
    follow_time_end: int | None = Field(default=None, description='跟进结束时间')
    admin_id_filter: int | None = Field(default=None, description='创建人 ID 筛选')


class AddCustomerTraceModel(CustomerTraceModel):
    """
    新增客户跟进记录模型
    """

    pass


class EditCustomerTraceModel(AddCustomerTraceModel):
    """
    编辑客户跟进记录模型
    """

    pass


class DeleteCustomerTraceModel(BaseModel):
    """
    删除客户跟进记录模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的跟进记录 ID')

