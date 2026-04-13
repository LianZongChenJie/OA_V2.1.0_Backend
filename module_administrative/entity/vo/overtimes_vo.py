from datetime import datetime
from typing import Literal, Any, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss
from decimal import Decimal


class OvertimesModel(BaseModel):
    """
    加班表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    start_date: Union[int, str, None] = Field(default=None, description='开始日期')
    end_date: Union[int, str, None] = Field(default=None, description='结束日期')
    start_span: int | None = Field(default=None, description='时间段:1上午,2下午')
    end_span: int | None = Field(default=None, description='时间段:1上午,2下午')
    duration: Decimal | None = Field(default=None, description='时长(工作日)')
    reason: str | None = Field(default=None, description='出差原因')
    file_ids: str | None = Field(default=None, description='附件，如:1,2,3')
    check_status: int | None = Field(default=None, description='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id: int | None = Field(default=None, description='审核流程id')
    check_step_sort: int | None = Field(default=None, description='当前审批步骤')
    check_uids: str | None = Field(default=None, description='当前审批人ID，如:1,2,3')
    check_last_uid: str | None = Field(default=None, description='上一审批人')
    check_history_uids: str | None = Field(default=None, description='历史审批人ID，如:1,2,3')
    check_copy_uids: str | None = Field(default=None, description='抄送人ID，如:1,2,3')
    check_time: Union[int, str, None] = Field(default=None, description='审核通过时间')
    admin_id: int | None = Field(default=None, description='创建人ID')
    did: int | None = Field(default=None, description='创建人部门ID')
    create_time: Union[int, str, None] = Field(default=None, description='创建时间')
    update_time: Union[int, str, None] = Field(default=None, description='更新时间')
    delete_time: Union[int, str, None] = Field(default=None, description='删除时间')

    @field_validator('start_date', mode='before')
    @classmethod
    def validate_start_date(cls, value: Any) -> int | None:
        """
        验证并转换开始日期字段，支持时间戳和日期字符串
        """
        if value is None or value == '':
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp())
            except ValueError:
                try:
                    return int(value)
                except ValueError:
                    pass

        return value

    @field_validator('end_date', mode='before')
    @classmethod
    def validate_end_date(cls, value: Any) -> int | None:
        """
        验证并转换结束日期字段，支持时间戳和日期字符串
        """
        if value is None or value == '':
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp())
            except ValueError:
                try:
                    return int(value)
                except ValueError:
                    pass

        return value

    @field_validator('create_time', mode='before')
    @classmethod
    def validate_create_time(cls, v):
        """处理 create_time 字段，支持时间戳整数或日期字符串"""
        if v is None or v == '':
            return None
        return v

    @field_validator('update_time', mode='before')
    @classmethod
    def validate_update_time(cls, v):
        """处理 update_time 字段，支持时间戳整数或日期字符串"""
        if v is None or v == '':
            return None
        return v

    @field_validator('delete_time', mode='before')
    @classmethod
    def validate_delete_time(cls, v):
        """处理 delete_time 字段，支持时间戳整数或日期字符串"""
        if v is None or v == '' or v == 0:
            return None
        return v

    @Xss(field_name='reason', message='加班原因不能包含脚本字符')
    @Size(field_name='reason', min_length=0, max_length=65535, message='加班原因长度不能超过 65535 个字符')
    def get_reason(self) -> str | None:
        return self.reason

    def validate_fields(self) -> None:
        self.get_reason()


class OvertimesQueryModel(OvertimesModel):
    """
    加班记录不分页查询模型
    """
    pass


class OvertimesPageQueryModel(OvertimesQueryModel):
    """
    加班记录分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')
    keywords: str | None = Field(default=None, description='搜索关键词')


class AddOvertimesModel(OvertimesModel):
    """
    新增加班记录模型
    """
    pass


class EditOvertimesModel(AddOvertimesModel):
    """
    编辑加班记录模型
    """
    pass


class DeleteOvertimesModel(BaseModel):
    """
    删除加班记录模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的加班记录 ID')