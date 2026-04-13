from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApproveUnifiedModel(BaseModel):
    """
    统一审批列表模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='记录ID')
    admin_id: int | None = Field(default=None, description='创建人ID')
    did: int | None = Field(default=None, description='部门ID')
    create_time: int | str | None = Field(default=None, description='创建时间')
    check_status: Literal[0, 1, 2, 3, 4] | None = Field(default=None, description='审核状态')
    check_flow_id: int | None = Field(default=None, description='审核流程ID')
    check_step_sort: int | None = Field(default=None, description='当前审批步骤')
    check_uids: str | None = Field(default=None, description='当前审批人ID')
    check_last_uid: str | None = Field(default=None, description='上一审批人')
    check_history_uids: str | None = Field(default=None, description='历史审批人ID')
    check_copy_uids: str | None = Field(default=None, description='抄送人ID')
    check_time: int | str | None = Field(default=None, description='审核通过时间')
    table_name: str | None = Field(default=None, description='表名')
    check_name: str | None = Field(default=None, description='审批类型名称')
    invoice_type: str | None = Field(default=None, description='发票类型')
    types: str | None = Field(default=None, description='类型')

    # 扩展字段
    admin_name: str | None = Field(default=None, description='创建人姓名')
    department: str | None = Field(default=None, description='部门名称')
    check_status_str: str | None = Field(default=None, description='审核状态字符串')
    check_users: str | None = Field(default=None, description='当前审批人姓名')
    check_copy_users: str | None = Field(default=None, description='抄送人姓名')
    types_name: str | None = Field(default=None, description='类型名称')
    view_url: str | None = Field(default=None, description='查看URL')
    add_url: str | None = Field(default=None, description='新增URL')


class ApprovePageQueryModel(BaseModel):
    """
    审批分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    page: int = Field(default=1, description='当前页码')
    limit: int = Field(default=20, description='每页记录数')
    status: int = Field(default=0, description='状态筛选：0全部，1进行中，2已完成，3已拒绝')