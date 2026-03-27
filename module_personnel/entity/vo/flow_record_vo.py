from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp
from pydantic import field_serializer
from typing import Optional

class OaFlowRecordBaseModel(BaseModel):
    """审批记录基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    id: int | None = Field(None, description='ID')
    action_id: int | None = Field(None, description='审批内容ID')
    check_table: str | None = Field(None, description='审批数据表')
    flow_id: int | None = Field(None, description='审批模版流程id')
    step_id: int | None = Field(None, description='审批步骤ID')
    check_files: str | None = Field(None, description='审批附件')
    check_uid: int | None = Field(None, description='审批人ID')
    check_time: int | None = Field(None, description='审批时间')
    check_status: int | None = Field(None, description='审批状态:0发起,1通过,2拒绝,3撤销')
    content: str | None = Field(None, description='审批意见')
    delete_time: int | None = Field(None, description='删除时间')

    @field_serializer('check_time')
    def serialize_check_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('delete_time')
    def serialize_delete_time(self, value: Optional[int]) -> Optional[str]:
        """序列化删除时间"""
        return format_timestamp(value)