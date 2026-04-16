from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss

from utils.timeformat import format_timestamp


class ProjectStepModel(BaseModel):
    """
    项目阶段模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='阶段ID')
    project_id: int | None = Field(default=None, description='关联项目ID')
    title: str | None = Field(default=None, alias='name', description='阶段名称')
    director_uid: int | None = Field(default=None, description='阶段负责人ID')
    uids: str | None = Field(default=None, alias='memberUids', description='阶段成员ID')
    sort: int | None = Field(default=None, description='排序ID')
    is_current: int | None = Field(default=None, description='是否是当前阶段')
    start_time: int | None = Field(default=None, description='开始时间')
    end_time: int | None = Field(default=None, description='结束时间')
    remark: str | None = Field(default=None, description='阶段说明')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='修改时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    director_name: str | None = Field(default=None, description='阶段负责人姓名')
    member_names: list[str] | None = Field(default=None, description='阶段成员姓名列表')
    start_time_str: str | None = Field(default=None, description='开始时间字符串')
    end_time_str: str | None = Field(default=None, description='结束时间字符串')

    @field_serializer('start_time')
    def serialize_start_time(self, value: Optional[int]) -> Optional[str]:
        """序列化开始时间"""
        return format_timestamp(value)

    @field_serializer('end_time')
    def serialize_end_time(self, value: Optional[int]) -> Optional[str]:
        """序列化结束时间"""
        return format_timestamp(value)

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)


class ProjectModel(BaseModel):
    """
    项目表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='项目 ID')
    name: str | None = Field(default=None, description='项目名称')
    code: str | None = Field(default=None, description='项目编号')
    amount: float | None = Field(default=None, description='项目金额')
    cate_id: int | None = Field(default=None, description='分类 ID')
    customer_id: int | None = Field(default=None, description='关联客户 ID')
    contract_id: int | None = Field(default=None, description='关联合同协议 ID')
    admin_id: int | None = Field(default=None, description='创建人')
    director_uid: int | None = Field(default=None, description='项目负责人')
    did: int | None = Field(default=None, description='项目所属部门')
    start_time: int | None = Field(default=None, description='项目开始时间')
    end_time: int | None = Field(default=None, description='项目结束时间')
    status: Literal[0, 1, 2, 3, 4] | None = Field(default=None, description='状态：0 未设置，1 未开始，2 进行中，3 已完成，4 已关闭')
    content: str | None = Field(default=None, description='项目描述')
    create_time: int | None = Field(default=None, description='添加时间')
    update_time: int | None = Field(default=None, description='修改时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    # 扩展字段，用于列表展示
    cate_title: str | None = Field(default=None, description='分类名称')
    customer_name: str | None = Field(default=None, description='客户名称')
    contract_name: str | None = Field(default=None, description='合同名称')
    admin_name: str | None = Field(default=None, description='创建人姓名')
    director_name: str | None = Field(default=None, description='项目负责人姓名')
    dept_name: str | None = Field(default=None, description='部门名称')
    status_name: str | None = Field(default=None, description='状态名称')
    start_time_str: str | None = Field(default=None, description='开始时间字符串')
    end_time_str: str | None = Field(default=None, description='结束时间字符串')

    # 项目阶段列表
    stages: list[ProjectStepModel] | None = Field(default=None, description='项目阶段列表')

    @field_serializer('start_time')
    def serialize_start_time(self, value: Optional[int]) -> Optional[str]:
        """序列化开始时间"""
        return format_timestamp(value)

    @field_serializer('end_time')
    def serialize_end_time(self, value: Optional[int]) -> Optional[str]:
        """序列化结束时间"""
        return format_timestamp(value)

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)

    @Xss(field_name='name', message='项目名称不能包含脚本字符')
    @NotBlank(field_name='name', message='项目名称不能为空')
    @Size(field_name='name', min_length=0, max_length=255, message='项目名称长度不能超过 255 个字符')
    def get_name(self) -> str | None:
        return self.name

    @Xss(field_name='code', message='项目编号不能包含脚本字符')
    @Size(field_name='code', min_length=0, max_length=255, message='项目编号长度不能超过 255 个字符')
    def get_code(self) -> str | None:
        return self.code

    @Xss(field_name='content', message='项目描述不能包含脚本字符')
    @Size(field_name='content', min_length=0, max_length=16777215, message='项目描述长度超出限制')
    def get_content(self) -> str | None:
        return self.content

    def validate_fields(self) -> None:
        self.get_name()
        self.get_code()
        self.get_content()


class ProjectPageQueryModel(ProjectModel):
    """
    项目分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    tab: int | None = Field(default=0, description='标签页：0 全部，1 进行中，2 即将到期，3 已逾期')
    status_filter: int | None = Field(default=None, description='状态筛选')
    cate_id_filter: int | None = Field(default=None, description='分类筛选')
    director_uid_filter: list[int] | None = Field(default=None, description='负责人筛选')


class AddProjectModel(ProjectModel):
    """
    新增项目模型
    """

    pass


class EditProjectModel(AddProjectModel):
    """
    编辑项目模型
    """

    pass


class DeleteProjectModel(BaseModel):
    """
    删除项目模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的项目 ID')
