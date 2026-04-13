from typing import Literal, Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class OfficialDocsModel(BaseModel):
    """
    公文表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='公文 ID')
    title: str | None = Field(default=None, description='公文主题')
    code: str | None = Field(default=None, description='公文编号')
    secrets: Literal[1, 2, 3] | None = Field(default=None, description='密级程度:1 公开，2 秘密，3 机密')
    urgency: Literal[1, 2, 3] | None = Field(default=None, description='紧急程度:1 普通，2 紧急，3 加急')
    send_uids: str | None = Field(default=None, description='主送 uid')
    copy_uids: str | None = Field(default=None, description='抄送 uid')
    share_uids: str | None = Field(default=None, description='分享查阅 uid')
    content: str | None = Field(default=None, description='公文内容')
    file_ids: str | None = Field(default=None, description='附件 ids，如:1,2,3')
    draft_uid: int | None = Field(default=None, description='拟稿人')
    did: int | None = Field(default=None, description='拟稿部门')
    draft_time: int | str | None = Field(default=None, description='拟稿日期')
    admin_id: int | None = Field(default=None, description='创建人')
    create_time: int | str | None = Field(default=None, description='创建时间')
    update_time: int | str | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')
    check_status: Literal[0, 1, 2, 3, 4] | None = Field(default=None, description='审核状态:0 待审核，1 审核中，2 审核通过，3 审核不通过，4 撤销审核')
    check_flow_id: int | None = Field(default=None, description='审核流程 id')
    check_step_sort: int | None = Field(default=None, description='当前审批步骤')
    check_uids: str | None = Field(default=None, description='当前审批人 ID，如:1,2,3')
    check_last_uid: str | None = Field(default=None, description='上一审批人')
    check_history_uids: str | None = Field(default=None, description='历史审批人 ID，如:1,2,3')
    check_copy_uids: str | None = Field(default=None, description='抄送人 ID，如:1,2,3')
    check_time: int | str | None = Field(default=None, description='审核通过时间')

    # 扩展字段，用于列表展示
    secrets_str: str | None = Field(default=None, description='密级字符串')
    urgency_str: str | None = Field(default=None, description='紧急程度字符串')
    check_status_str: str | None = Field(default=None, description='审核状态字符串')
    draft_name: str | None = Field(default=None, description='拟稿人姓名')
    draft_dname: str | None = Field(default=None, description='拟稿部门名称')
    send_names: str | None = Field(default=None, description='主送人姓名列表')
    copy_names: str | None = Field(default=None, description='抄送人姓名列表')
    share_names: str | None = Field(default=None, description='分享查阅人姓名列表')
    file_array: list | None = Field(default=None, description='附件数组')

    @field_validator('secrets', mode='before')
    @classmethod
    def validate_secrets(cls, value: Any) -> int | None:
        """
        验证并转换密级字段，支持字符串和整数
        """
        if value is None or value == '':
            return None
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                pass
        
        return value

    @field_validator('urgency', mode='before')
    @classmethod
    def validate_urgency(cls, value: Any) -> int | None:
        """
        验证并转换紧急程度字段，支持字符串和整数
        """
        if value is None or value == '':
            return None
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                pass
        
        return value

    @field_validator('draft_time', mode='before')
    @classmethod
    def validate_draft_time(cls, value: Any) -> int | str | None:
        """
        验证并转换拟稿日期字段，支持时间戳和日期字符串
        """
        if value is None or value == '':
            return None
        
        if isinstance(value, (int, str)):
            return value
        
        return value

    @field_validator('create_time', mode='before')
    @classmethod
    def validate_create_time(cls, value: Any) -> int | str | None:
        """
        验证并转换创建时间字段，支持时间戳和日期字符串
        """
        if value is None or value == '':
            return None
        
        if isinstance(value, (int, str)):
            return value
        
        return value

    @field_validator('update_time', mode='before')
    @classmethod
    def validate_update_time(cls, value: Any) -> int | str | None:
        """
        验证并转换更新时间字段，支持时间戳和日期字符串
        """
        if value is None or value == '':
            return None
        
        if isinstance(value, (int, str)):
            return value
        
        return value

    @field_validator('check_time', mode='before')
    @classmethod
    def validate_check_time(cls, value: Any) -> int | str | None:
        """
        验证并转换审核时间字段，支持时间戳和日期字符串
        """
        if value is None or value == '':
            return None
        
        if isinstance(value, (int, str)):
            return value
        
        return value

    @Xss(field_name='title', message='公文主题不能包含脚本字符')
    @NotBlank(field_name='title', message='公文主题不能为空')
    @Size(field_name='title', min_length=0, max_length=255, message='公文主题长度不能超过 255 个字符')
    def get_title(self) -> str | None:
        return self.title

    @Xss(field_name='code', message='公文编号不能包含脚本字符')
    @Size(field_name='code', min_length=0, max_length=100, message='公文编号长度不能超过 100 个字符')
    def get_code(self) -> str | None:
        return self.code

    def validate_fields(self) -> None:
        self.get_title()
        self.get_code()


class OfficialDocsPageQueryModel(OfficialDocsModel):
    """
    公文分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    tab: int | None = Field(default=0, description='标签页：0 全部，1 我创建的，2 待我审批，3 我已审批，4 我抄送的')
    secrets_filter: int | None = Field(default=None, alias='secrets', description='密级筛选')
    urgency_filter: int | None = Field(default=None, alias='urgency', description='紧急程度筛选')

    @field_validator('secrets_filter', mode='before')
    @classmethod
    def validate_secrets_filter(cls, value: Any) -> int | None:
        """
        验证并转换密级筛选项
        """
        if value is None or value == '':
            return None
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                pass
        
        return None

    @field_validator('urgency_filter', mode='before')
    @classmethod
    def validate_urgency_filter(cls, value: Any) -> int | None:
        """
        验证并转换紧急程度筛选项
        """
        if value is None or value == '':
            return None
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                pass
        
        return None


class AddOfficialDocsModel(OfficialDocsModel):
    """
    新增公文模型
    """

    pass


class EditOfficialDocsModel(AddOfficialDocsModel):
    """
    编辑公文模型
    """

    pass


class DeleteOfficialDocsModel(BaseModel):
    """
    删除公文模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的公文 ID')


class PendingOfficialDocsModel(OfficialDocsPageQueryModel):
    """
    待审公文查询模型
    """

    pass


class ReviewedOfficialDocsModel(OfficialDocsPageQueryModel):
    """
    已审公文查询模型
    """

    pass
