from email.policy import default

from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.timeformat import format_timestamp
from pydantic import field_serializer
from typing import Optional,List

class OaPersonalQuitBaseModel(BaseModel):
    """离职申请 VO - 用于数据展示"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='主键ID')
    uid: int | None = Field(default=None, description='用户ID')
    lead_admin_id: int | None  = Field(default=None, description='上级领导')
    connect_id: int | None  = Field(default=None, description='资料交接人')
    connect_time: int | None  = Field(default=None, description='资料交接时间')
    connect_uids: str = Field(default=None, description='参与交接人')
    connect_uids_list: Optional[List[int]] = Field(None, description='参与交接人列表')
    file_ids: str = Field(default=None, description='档案附件')
    file_ids_list: Optional[List[str]] = Field(None, description='档案附件列表')
    quit_time: int | None  = Field(default=None, description='离职时间')
    status: int | None  = Field(default=None, description='状态')
    status_name:  str | None  = Field(None, description='状态名称')
    remark:  str | None  = Field(None, description='备注信息')
    admin_id: int | None  = Field(default=None, description='创建人')
    did: int | None  = Field(default=None, description='创建人所在部门')
    check_status: int | None  = Field(default=None, description='审核状态')
    check_status_name:  str | None  = Field(None, description='审核状态名称')
    check_flow_id: int | None  = Field(default=None, description='审核流程id')
    check_step_sort: int | None  = Field(default=None, description='当前审批步骤')
    check_uids: str | None  = Field(default=None, description='当前审批人ID')
    check_uids_list: Optional[List[int]] = Field(None, description='当前审批人ID列表')
    check_last_uid: str | None  = Field(default=None, description='上一审批人')
    check_history_uids: str | None  = Field(default=None, description='历史审批人ID')
    check_history_uids_list: Optional[List[int]] = Field(None, description='历史审批人ID列表')
    check_copy_uids: str | None  = Field(default=None, description='抄送人ID')
    check_copy_uids_list: Optional[List[int]] = Field(None, description='抄送人ID列表')
    check_time: int | None  = Field(default=None, description='审核通过时间')
    check_time_str:  str | None  = Field(None, description='审核通过时间（字符串格式）')
    create_time: int | None  = Field(default=None, description='创建时间')
    create_time_str:  str | None  = Field(None, description='创建时间（字符串格式）')
    update_time: int | None  = Field(default=None, description='更新时间')
    delete_time: int | None  = Field(default=None, description='删除时间')

    @field_serializer('connect_time')
    def serialize_connect_time(self, value: Optional[int]) -> Optional[str]:
        """序列化移交资料时间"""
        return format_timestamp(value)

    @field_serializer('quit_time')
    def serialize_quit_time(self, value: Optional[int]) -> Optional[str]:
        """序列化离职时间"""
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

    @field_serializer('check_time')
    def serialize_check_time(self, value: Optional[int]) -> Optional[str]:
        """序列化审核时间"""
        return format_timestamp(value)



class OaPersonnelQuitQueryModel(OaPersonalQuitBaseModel):
    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')

class OaPersonnelQuitPageQueryModel(OaPersonnelQuitQueryModel):
    """离职分页申请查询VO"""
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')

class OaPersonnelQuitDetailModel(BaseModel):
    """离职申请详情VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    info : OaPersonalQuitBaseModel|None = Field(default=None, description='离职申请详情')
    records : list[OaFlowRecordBaseModel]|None = Field(default=None, description='离职申请审批记录')
