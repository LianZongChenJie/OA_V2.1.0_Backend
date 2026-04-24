from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class ProjectDocumentModel(BaseModel):
    """
    项目文档表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='文档ID')
    project_id: int | None = Field(default=None, description='项目ID')
    admin_id: int | None = Field(default=None, description='创建人ID')
    title: str | None = Field(default=None, description='文档标题')
    did: int | None = Field(default=None, description='所属部门ID')
    file_ids: str | None = Field(default=None, description='附件IDs')
    content: str | None = Field(default=None, description='文档内容')
    md_content: str | None = Field(default=None, description='Markdown文档内容')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')
    
    # 关联字段
    project_name: str | None = Field(default=None, description='项目名称')
    admin_name: str | None = Field(default=None, description='创建人姓名')
    user_name: str | None = Field(default=None, description='创建人用户名')
    create_time_str: str | None = Field(default=None, description='创建时间字符串')
    update_time_str: str | None = Field(default=None, description='更新时间字符串')

    @Xss(field_name='title', message='文档标题不能包含脚本字符')
    @NotBlank(field_name='title', message='文档标题不能为空')
    @Size(field_name='title', min_length=0, max_length=255, message='文档标题长度不能超过255个字符')
    def get_title(self) -> str | None:
        return self.title

    def validate_fields(self) -> None:
        self.get_title()


class ProjectDocumentPageQueryModel(ProjectDocumentModel):
    """
    项目文档分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键字')


class AddProjectDocumentModel(ProjectDocumentModel):
    """
    新增项目文档模型
    """

    pass


class EditProjectDocumentModel(AddProjectDocumentModel):
    """
    编辑项目文档模型
    """

    pass


class DeleteProjectDocumentModel(BaseModel):
    """
    删除项目文档模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的文档ID')
