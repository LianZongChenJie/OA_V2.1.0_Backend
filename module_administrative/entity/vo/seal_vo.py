from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.timeformat import format_timestamp
from typing import Optional


class OaSealBaseModel(BaseModel):
    """用章申请基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None= Field(None, description='主键ID')
    title: str | None = Field(None, description='用章申请主题')
    seal_cate_id: int | None= Field(None, description='印章类型')
    content: str | None = Field(None, description='盖章内容')
    file_ids: str | None = Field(None, description='附件ids,如:1,2,3')
    did: int | None= Field(None, description='用印部门')
    num: int | None= Field(None, description='盖章次数')
    use_time: int | str |None= Field(None, description='预期用印日期')
    is_borrow: int | None= Field(None, description='印章是否外借:0,1')
    start_time: int | str | None = Field(None, description='印章借用日期')
    end_time: int | str | None= Field(None, description='结束借用日期')
    status: int | None= Field(None, description='状态:0待使用,1已使用(已外借),2已结束归还')
    admin_id: int | None= Field(None, description='创建人')
    create_time: int | None= Field(None, description='创建时间')
    update_time: int | None= Field(None, description='更新时间')
    delete_time: int | None= Field(None, description='删除时间')
    check_status: int | None= Field(None, description='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id: int | None= Field(None, description='审核流程id')
    check_step_sort: int | None= Field(None, description='当前审批步骤')
    check_uids: str | None = Field(None, description='当前审批人ID，如:1,2,3')
    check_last_uid: str | None = Field(None, description='上一审批人')
    check_history_uids: str | None = Field(None, description='历史审批人ID，如:1,2,3')
    check_copy_uids: str | None = Field(None, description='抄送人ID，如:1,2,3')
    check_time: int | None= Field(None, description='审核通过时间')


    # 关联字段
    did_name: Optional[str] = None
    admin_name: Optional[str] = None
    check_last_name: Optional[str] = None
    check_user_names: Optional[list] = None
    check_user_names_str: Optional[str] = None
    check_history_names: Optional[list] = None
    check_history_names_str: Optional[str] = None

    @field_serializer('use_time')
    def serialize_use_time(self, value: Optional[int]) -> Optional[str]:
        """序列化使用时间"""
        return format_timestamp(value)

    @field_serializer('start_time')
    def serialize_start_time(self, value: Optional[int]) -> Optional[str]:
        """序列化开始时间"""
        return format_timestamp(value)

    @field_serializer('end_time')
    def serialize_end_time(self, value: Optional[int]) -> Optional[str]:
        """序列化结束时间"""
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

class OaSealPageQueryModel(OaSealBaseModel):
    """用章申请分页查询VO"""
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')
    keyword: str | None = Field(None, description='关键字')


class OaSealDetail(BaseModel):
    """人事调动申请详情VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    info : OaSealBaseModel = Field(default=None,description='用章申请详情')
    records : list[OaFlowRecordBaseModel] = Field(default=None, description='用章申请审批记录')