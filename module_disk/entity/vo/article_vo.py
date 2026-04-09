"""
在线文档相关 Pydantic 模型
"""
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class ArticleModel(BaseModel):
    """
    在线文档表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='文档ID')
    name: str | None = Field(default=None, description='文档标题')
    origin_url: str | None = Field(default=None, description='来源地址')
    file_ids: str | None = Field(default=None, description='相关附件')
    content: str | None = Field(default=None, description='文章内容')
    admin_id: int | None = Field(default=None, description='作者')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    @Xss(field_name='name', message='文档标题不能包含脚本字符')
    @NotBlank(field_name='name', message='文档标题不能为空')
    @Size(field_name='name', min_length=0, max_length=255, message='文档标题长度不能超过255个字符')
    def get_name(self) -> str | None:
        return self.name

    def validate_fields(self) -> None:
        self.get_name()


class AddArticleModel(ArticleModel):
    """
    新增在线文档模型
    """
    pass


class EditArticleModel(AddArticleModel):
    """
    编辑在线文档模型
    """
    id: int = Field(description='文档ID')
