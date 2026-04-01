from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.timeformat import format_timestamp
from pydantic import field_serializer
from typing import Optional
class OaDepartmentChangeBassModel(BaseModel):
    """人事调动申请基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    uid: int | None = Field(None, description='员工ID')
    from_did: int | None = Field(None, description='原部门id')
    to_did: int | None = Field(None, description='调到部门id')
    connect_id: int | None = Field(None, description='资料交接人')
    connect_time: int | None = Field(None, description='资料交接时间')
    connect_uids: str | None = Field(None, description='参与交接人,可多个')
    file_ids: str | None = Field(None, description='档案附件')
    move_time: int | None = Field(None, description='调动时间')
    status: int | None = Field(None, description='状态:1未调动,2已交接调动')
    remark: str | None = Field(None, description='备注信息')
    admin_id: int | None = Field(None, description='创建人')
    did: int | None = Field(None, description='创建人所在部门')
    check_status: int | None = Field(None, description='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id: int | None = Field(None, description='审核流程id')
    check_step_sort: int | None = Field(None, description='当前审批步骤')
    check_uids: str | None = Field(None, description='当前审批人ID，如:1,2,3')
    check_last_uid: str | None = Field(None, description='上一审批人')
    check_history_uids: str | None = Field(None, description='历史审批人ID，如:1,2,3')
    check_copy_uids: str | None = Field(None, description='抄送人ID，如:1,2,3')
    check_time: int | None = Field(None, description='审核通过时间')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')
    delete_time: int | None = Field(None, description='删除时间')

    @field_serializer('move_time')
    def serialize_move_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

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
        return format_timestamp(value)

class OaDepartmentChangeQueryModel(OaDepartmentChangeBassModel):
    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')

class OaDepartmentChangePageQueryModel(OaDepartmentChangeQueryModel):
    """人事调动申请分页查询VO"""
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')

class OaDepartmentChangeDetailModel(BaseModel):
    """人事调动申请详情VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    info : OaDepartmentChangeBassModel | None = Field(..., description='人事调动申请详情')
    records : list[OaFlowRecordBaseModel] | None = Field(..., description='人事调动申请审批记录')