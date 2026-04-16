from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class SubmitCheckRequest(BaseModel):
    """提交审批申请请求模型"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    action_id: int = Field(description='审批内容ID')
    flow_id: int = Field(description='流程ID')
    check_name: str = Field(description='审批类型名称')
    check_uids: str | None = Field(default=None, description='指定审批人IDs')
    check_copy_uids: str | None = Field(default='', description='抄送人IDs')


class FlowCheckRequest(BaseModel):
    """流程审核请求模型"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    action_id: int = Field(description='审批内容ID')
    check_name: str = Field(description='审批类型名称')
    check: int = Field(description='审核操作：1通过 2拒绝 3撤回 4反确认')
    content: str = Field(default='', description='审批意见')
    check_files: str | None = Field(default='', description='审批附件')
    check_uids: str | None = Field(default=None, description='下一步审批人')
    check_node: int | None = Field(default=1, description='是否继续添加节点')
