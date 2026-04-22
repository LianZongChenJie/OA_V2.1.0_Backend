from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from typing import Optional

class OaFlowStepBaseModel(BaseModel):
    """审批步骤基础模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    flow_name: str | None = Field(None, description='流程步骤名称')
    action_id: int | None = Field(None, description='审批内容ID')
    flow_id: int | None = Field(None, description='审批流程id')
    check_role: int | None = Field(None,
                                      description='审批角色:0自由指定,1当前部门负责人,2上一级部门负责人,3指定职位,4指定用户,5可回退审批')
    check_position_id: int | None = Field(None, description='审批角色id')
    check_uids: str | None = Field(None, description='审批人ids(1,2,3)')
    check_types: int | None = Field(None, description='审批方式:1会签2或签')
    sort: int | None = Field(None, description='排序ID')
    create_time: int | None = Field(None, description='创建时间')
    delete_time: int | None = Field(None, description='删除时间')