from typing import Literal, Any
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class TripsModel(BaseModel):
    """
    出差表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='出差 ID')
    start_date: int | str | None = Field(default=None, description='开始日期')
    end_date: int | str | None = Field(default=None, description='结束日期')
    start_span: Literal[1, 2] | None = Field(default=None, description='时间段:1上午,2下午')
    end_span: Literal[1, 2] | None = Field(default=None, description='时间段:1上午,2下午')
    duration: Decimal | float | None = Field(default=None, description='时长(工作日)')
    reason: str | None = Field(default=None, description='出差原因')
    file_ids: str | None = Field(default=None, description='附件 ids')
    check_status: Literal[0, 1, 2, 3, 4] | None = Field(default=None, description='审核状态')
    check_flow_id: int | None = Field(default=None, description='审核流程 id')
    check_step_sort: int | None = Field(default=None, description='当前审批步骤')
    check_uids: str | None = Field(default=None, description='当前审批人 ID')
    check_last_uid: str | None = Field(default=None, description='上一审批人')
    check_history_uids: str | None = Field(default=None, description='历史审批人 ID')
    check_copy_uids: str | None = Field(default=None, description='抄送人 ID')
    check_time: int | None = Field(default=None, description='审核通过时间')
    admin_id: int | None = Field(default=None, description='创建人ID')
    did: int | None = Field(default=None, description='创建人部门ID')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    admin_name: str | None = Field(default=None, description='创建人姓名')
    dept_name: str | None = Field(default=None, description='部门名称')

    @field_validator('start_date', mode='before')
    @classmethod
    def validate_start_date(cls, value: Any) -> int | None:
        """验证并转换开始时间"""
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
        """验证并转换结束时间"""
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

    @Xss(field_name='reason', message='出差原因不能包含脚本字符')
    @NotBlank(field_name='reason', message='出差原因不能为空')
    def get_reason(self) -> str | None:
        return self.reason

    def validate_fields(self) -> None:
        self.get_reason()


class TripsPageQueryModel(TripsModel):
    """
    出差分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')


class AddTripsModel(TripsModel):
    """
    新增出差模型
    """

    pass


class EditTripsModel(AddTripsModel):
    """
    编辑出差模型
    """

    pass


class DeleteTripsModel(BaseModel):
    """
    删除出差模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的出差 ID')