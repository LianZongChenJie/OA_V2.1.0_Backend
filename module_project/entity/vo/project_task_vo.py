from typing import Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class ProjectTaskModel(BaseModel):
    """
    项目任务表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='任务 ID')
    title: str | None = Field(default=None, description='主题')
    pid: int | None = Field(default=None, description='父级任务 id')
    before_task: int | None = Field(default=None, description='前置任务 id')
    project_id: int | None = Field(default=None, description='关联项目 id')
    work_id: int | None = Field(default=None, description='关联工作类型')
    step_id: int | None = Field(default=None, description='关联项目阶段')
    plan_hours: float | None = Field(default=None, description='预估工时')
    end_time: int | None = Field(default=None, description='预计结束时间')
    over_time: int | None = Field(default=None, description='实际结束时间')
    admin_id: int | None = Field(default=None, description='创建人')
    director_uid: int | None = Field(default=None, description='指派给 (负责人)')
    did: int | None = Field(default=None, description='所属部门')
    assist_admin_ids: str | None = Field(default=None, description='协助人员，如:1,2,3')
    priority: int | None = Field(default=None, description='优先级:1 低，2 中，3 高，4 紧急')
    status: int | None = Field(default=None, description='任务状态：1 待办的，2 进行中，3 已完成，4 已拒绝，5 已关闭')
    done_ratio: int | None = Field(default=None, description='完成进度：0,20,40,50,60,80')
    content: str | None = Field(default=None, description='任务描述')
    create_time: int | None = Field(default=None, description='添加时间')
    update_time: int | None = Field(default=None, description='修改时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    # 扩展字段，用于列表展示
    project_name: str | None = Field(default=None, description='项目名称')
    admin_name: str | None = Field(default=None, description='创建人姓名')
    director_name: str | None = Field(default=None, description='负责人姓名')
    dept_name: str | None = Field(default=None, description='部门名称')
    priority_name: str | None = Field(default=None, description='优先级名称')
    status_name: str | None = Field(default=None, description='状态名称')
    work_name: str | None = Field(default=None, description='工作类型名称')
    end_time_str: str | None = Field(default=None, description='结束时间字符串')
    create_time_str: str | None = Field(default=None, description='创建时间字符串')
    update_time_str: str | None = Field(default=None, description='更新时间字符串')
    over_time_str: str | None = Field(default=None, description='实际结束时间字符串')

    @Xss(field_name='title', message='任务主题不能包含脚本字符')
    @NotBlank(field_name='title', message='任务主题不能为空')
    @Size(field_name='title', min_length=0, max_length=255, message='任务主题长度不能超过 255 个字符')
    def get_title(self) -> str | None:
        return self.title

    @Xss(field_name='content', message='任务描述不能包含脚本字符')
    @Size(field_name='content', min_length=0, max_length=16777215, message='任务描述长度超出限制')
    def get_content(self) -> str | None:
        return self.content

    def validate_fields(self) -> None:
        self.get_title()
        self.get_content()


class ProjectTaskPageQueryModel(ProjectTaskModel):
    """
    项目任务分页查询模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    tab: int | None = Field(default=0, description='标签页：0 全部，1 进行中，2 即将逾期，3 已逾期')
    
    # 支持两种命名方式：status_filter 和 statusName
    status_filter: int | None = Field(default=None, alias='statusName', description='状态筛选')
    priority_filter: int | None = Field(default=None, alias='priorityName', description='优先级筛选')
    work_id_filter: int | None = Field(default=None, alias='workId', description='工作类型筛选')
    project_id_filter: int | None = Field(default=None, alias='projectId', description='项目筛选')
    director_uid_filter: str | None = Field(default=None, alias='directorUid', description='负责人筛选（支持多个，逗号分隔）')

    @field_validator('director_uid_filter', mode='before')
    @classmethod
    def validate_director_uid_filter(cls, v):
        """处理 directorUid 参数，支持单个值、数组或逗号分隔的字符串"""
        if v is None:
            return None
        
        # 如果已经是列表，转换为逗号分隔的字符串
        if isinstance(v, list):
            values = [str(int(x)) for x in v if x is not None and str(x).strip()]
            return ','.join(values) if values else None
        
        # 如果是单个值，直接返回字符串
        if isinstance(v, (int, str)):
            v_str = str(v).strip()
            return v_str if v_str else None
        
        return None
    
    def get_director_uid_list(self) -> list[int] | None:
        """获取负责人 ID 列表"""
        if not self.director_uid_filter:
            return None
        
        try:
            # 支持逗号分隔
            uid_list = [int(uid.strip()) for uid in self.director_uid_filter.split(',') if uid.strip()]
            return uid_list if uid_list else None
        except (ValueError, AttributeError):
            return None


class AddProjectTaskModel(ProjectTaskModel):
    """
    新增项目任务模型
    """

    pass


class EditProjectTaskModel(AddProjectTaskModel):
    """
    编辑项目任务模型
    """

    pass


class DeleteProjectTaskModel(BaseModel):
    """
    删除项目任务模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的任务 ID')
