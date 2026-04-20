from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from typing import Optional
from utils.timeformat import format_timestamp

class OaFlowBaseModel(BaseModel):
    """审批基础模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: Optional[int] = Field(None, description='ID')
    title: Optional[str] = Field(None, description='审批流程名称')
    cate_id: Optional[int] = Field(None, description='关联审批类型id')
    check_type: Optional[int] = Field(None, description='1自由审批流,2固定审批流,3固定可回退的审批流,4固定条件审批流')
    department_ids: Optional[str] = Field(None, description='应用部门ID（0为全部）1,2,3')
    copy_uids: Optional[str] = Field(None, description='抄送人ID')
    flow_list: Optional[str] = Field(None, description='流程数据序列化')
    status: Optional[int] = Field(None, description='状态 1启用，0禁用')
    remark: Optional[str] = Field(None, description='流程说明')
    admin_id: Optional[int] = Field(None, description='创建人ID')
    create_time: Optional[int] = Field(None, description='创建时间')
    update_time: Optional[int] = Field(None, description='更新时间')
    delete_time: Optional[int] = Field(None, description='删除时间')


    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)

    @field_serializer('delete_time')
    def serialize_delete_time(self, value: Optional[int]) -> Optional[str]:
        """序列化删除时间"""
        return format_timestamp(value) if value else None

class OaFlowPageQueryModel(OaFlowBaseModel):
    """审批分页查询模型"""
    page_num: Optional[int] = Field(1, description='当前页码')
    page_size: Optional[int] = Field(10, description='每页数量')

class OaFlowVOModel(OaFlowBaseModel):
    """审批视图模型"""
    cate_name: Optional[str] = Field(None, description='审批类型名称')
    module_name: Optional[str] = Field(None, description='审批模块名称')
    copy_names: Optional[str] = Field(None, description='抄送人名称')
    department_names: Optional[str] = Field(None, description='应用部门名称')

class OaFlowAndStepModel(OaFlowBaseModel):
    check_role : int | None = Field(None, description='角色ID')
    check_position_id : int | None = Field(None, description='岗位ID')
    check_types : int | None = Field(None, description='审批类型')
    check_uids : str | None = Field(None, description='审批用户')
    action_id : int | None = Field(None, description='动作ID')

class OaFlowCheckBaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    check: int = Field(None, description='审批状态1:通过, 2:拒绝, 3:撤销, 4:反确认')
    content : str | None = Field(None, description='审批意见')
    action_id: int = Field(None, description='审批动作ID')
    type: str| None = Field(None, description='审批类型')
    flow_id: int | None = Field(None, description='审批流程ID')
    check_files: str | None = Field(None, description='审批文件ID')
    check_name: str | None = Field(None, description='审批人名称')
    check_uids : str | None = Field(None, description='审批人ID')
    check_copy_uids: str | None = Field(None, description='抄送人ID')
    check_node : int | None = Field(None, description='审批节点')
    check_status : int | None = Field(None, description='审批状态')

class OaFlowListBaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    check_role: int | None = Field(None, description='审批步骤类型 1当前部门负责人， 2上一级部门负责人，3指定岗位，4指定成员，5可回退审核')
    check_position_id : int | None = Field(None, description='岗位ID')
    check_types : int | None = Field(None, description='审批类型 1或签，2会签')
    check_uids : str | None = Field(None, description='审批用户id')
    flow_name : str | None = Field(None, description='审批流程名称')