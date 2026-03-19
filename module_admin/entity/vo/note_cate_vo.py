from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class NoteCateModel(BaseModel):
    """
    公告分类表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='公告分类 ID')
    pid: int | None = Field(default=0, description='父类 ID')
    sort: int | None = Field(default=0, description='排序')
    title: str | None = Field(default=None, description='标题')
    status: Literal[-1, 0, 1] | None = Field(default=1, description='1 可用 -1 禁用')
    create_time: int | None = Field(default=None, description='添加时间')
    update_time: int | None = Field(default=None, description='修改时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    @Xss(field_name='title', message='标题不能包含脚本字符')
    @NotBlank(field_name='title', message='标题不能为空')
    @Size(field_name='title', min_length=0, max_length=50, message='标题长度不能超过 50 个字符')
    def get_title(self) -> str | None:
        return self.title

    def validate_fields(self) -> None:
        self.get_title()


class NoteCatePageQueryModel(NoteCateModel):
    """
    公告分类分页查询模型
    """

    pass


class AddNoteCateModel(NoteCateModel):
    """
    新增公告分类模型
    """

    pass


class EditNoteCateModel(AddNoteCateModel):
    """
    编辑公告分类模型
    """

    pass


class DeleteNoteCateModel(BaseModel):
    """
    删除公告分类模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='公告分类 ID')


class SetNoteCateModel(BaseModel):
    """
    设置公告分类状态模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='公告分类 ID')
    status: Literal[0, 1] = Field(description='状态：0 禁用 1 启用')

