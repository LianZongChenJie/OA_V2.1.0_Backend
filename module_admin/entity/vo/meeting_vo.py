from datetime import datetime
from typing import Any, Optional
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss

from utils.timeformat import format_timestamp

# ==================== 会议室相关模型 ====================

class MeetingRoomModel(BaseModel):
    """
    会议室表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    title: str | None = Field(default=None, description='会议室名称')
    keep_uid: int | None = Field(default=None, description='会议室管理员 ID')
    address: str | None = Field(default=None, description='地址楼层')
    device: str | None = Field(default=None, description='会议室设备')
    num: int | None = Field(default=None, description='可容纳人数')
    remark: str | None = Field(default=None, description='会议室描述')
    status: int | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')

    # 关联查询返回的字段
    keep_name: str | None = Field(default=None, description='会议室管理员姓名')

    @Xss(field_name='remark', message='会议室描述不能包含脚本字符')
    @Size(field_name='remark', min_length=0, max_length=1000, message='会议室描述长度不能超过 1000 个字符')
    def get_remark(self) -> str | None:
        return self.remark

    def validate_fields(self) -> None:
        self.get_remark()


class MeetingRoomPageQueryModel(MeetingRoomModel):
    """
    会议室分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')


class AddMeetingRoomModel(MeetingRoomModel):
    """
    新增会议室模型
    """
    pass


class EditMeetingRoomModel(AddMeetingRoomModel):
    """
    编辑会议室模型
    """
    pass


class DeleteMeetingRoomModel(BaseModel):
    """
    删除会议室模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的会议室 ID')


class MeetingRoomStatusModel(BaseModel):
    """
    会议室状态更新模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='会议室 ID')
    status: int = Field(description='状态：-1 删除 0 禁用 1 启用')


# ==================== 会议室预定相关模型 ====================

class MeetingOrderModel(BaseModel):
    """
    会议室预定订单表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    room_id: int | None = Field(default=None, description='会议室 ID')
    title: str | None = Field(default=None, description='预定主题')
    start_date: int | None = Field(default=None, description='开始时间')
    end_date: int | None = Field(default=None, description='结束时间')
    admin_id: int | None = Field(default=None, description='发布人 id')
    did: int | None = Field(default=None, description='主办部门')
    requirements: str | None = Field(default=None, description='会议要求')
    num: int | None = Field(default=None, description='人数')
    remark: str | None = Field(default=None, description='备注信息')
    file_ids: str | None = Field(default=None, description='相关附件')
    join_uids: str | None = Field(default=None, description='与会人员')
    anchor_id: int | None = Field(default=None, description='主持人 id')
    check_status: int | None = Field(default=None, description='审核状态:0 待审核，1 审核中，2 审核通过，3 审核不通过，4 撤销审核')
    check_flow_id: int | None = Field(default=None, description='审核流程 id')
    check_step_sort: int | None = Field(default=None, description='当前审批步骤')
    check_uids: str | None = Field(default=None, description='当前审批人 ID，如:1,2,3')
    check_last_uid: str | None = Field(default=None, description='上一审批人')
    check_history_uids: str | None = Field(default=None, description='历史审批人 ID，如:1,2,3')
    check_copy_uids: str | None = Field(default=None, description='抄送人 ID，如:1,2,3')
    check_time: int | None = Field(default=None, description='审核通过时间')
    create_time: int | None = Field(default=None, description='申请时间')
    update_time: int | None = Field(default=None, description='更新信息时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    # 关联查询返回的字段
    room_name: str | None = Field(default=None, description='会议室名称')
    admin_name: str | None = Field(default=None, description='预定人姓名')
    dept_name: str | None = Field(default=None, description='部门名称')
    meeting_time_str: str | None = Field(default=None, description='会议时间字符串')

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def validate_date_fields(cls, value: Any) -> int | None:
        """
        验证并转换日期字段
        """
        if value is None:
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

    @Xss(field_name='title', message='预定主题不能包含脚本字符')
    @NotBlank(field_name='title', message='预定主题不能为空')
    def get_title(self) -> str | None:
        return self.title

    def validate_fields(self) -> None:
        self.get_title()


class MeetingOrderPageQueryModel(MeetingOrderModel):
    """
    会议室预定分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    room_id: int | None = Field(default=None, description='会议室 ID')
    check_status: int | None = Field(default=None, description='审核状态')
    diff_time: str | None = Field(default=None, description='时间范围')


class AddMeetingOrderModel(MeetingOrderModel):
    """
    新增会议室预定模型
    """
    pass


class EditMeetingOrderModel(AddMeetingOrderModel):
    """
    编辑会议室预定模型
    """
    pass


class DeleteMeetingOrderModel(BaseModel):
    """
    删除会议室预定模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的预定 ID')


# ==================== 会议纪要相关模型 ====================

class MeetingRecordsModel(BaseModel):
    """
    会议纪要表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    title: str | None = Field(default=None, description='会议主题')
    meeting_date: int | None = Field(default=None, description='会议时间')
    room_id: int | None = Field(default=None, description='会议室')
    did: int | None = Field(default=None, description='主办部门')
    content: str | None = Field(default=None, description='会议内容')
    plans: str | None = Field(default=None, description='下一步实施计划')
    file_ids: str | None = Field(default=None, description='相关附件')
    join_uids: str | None = Field(default=None, description='与会人员')
    sign_uids: str | None = Field(default=None, description='签到人员')
    share_uids: str | None = Field(default=None, description='共享给谁')
    anchor_id: int | None = Field(default=None, description='主持人 id')
    recorder_id: int | None = Field(default=None, description='记录人 id')
    remarks: str | None = Field(default=None, description='备注内容')
    admin_id: int | None = Field(default=None, description='发布人 id')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    # 关联查询返回的字段
    room_name: str | None = Field(default=None, description='会议室名称')
    dept_name: str | None = Field(default=None, description='部门名称')
    anchor_name: str | None = Field(default=None, description='主持人姓名')
    recorder_name: str | None = Field(default=None, description='记录人姓名')
    meeting_date_str: str | None = Field(default=None, description='会议时间字符串')
    create_time_str: str | None = Field(default=None, description='创建时间字符串')
    update_time_str: str | None = Field(default=None, description='更新时间字符串')

    @field_validator('meeting_date', mode='before')
    @classmethod
    def validate_meeting_date(cls, value: Any) -> int | None:
        """
        验证并转换会议日期字段
        """
        if value is None:
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

    @Xss(field_name='content', message='会议内容不能包含脚本字符')
    @Size(field_name='content', min_length=0, max_length=65535, message='会议内容长度不能超过 65535 个字符')
    def get_content(self) -> str | None:
        return self.content

    @Xss(field_name='plans', message='实施计划不能包含脚本字符')
    @Size(field_name='plans', min_length=0, max_length=65535, message='实施计划长度不能超过 65535 个字符')
    def get_plans(self) -> str | None:
        return self.plans

    @Xss(field_name='remarks', message='备注内容不能包含脚本字符')
    @Size(field_name='remarks', min_length=0, max_length=65535, message='备注内容长度不能超过 65535 个字符')
    def get_remarks(self) -> str | None:
        return self.remarks

    def validate_fields(self) -> None:
        self.get_content()
        self.get_plans()
        self.get_remarks()


class MeetingRecordsPageQueryModel(MeetingRecordsModel):
    """
    会议纪要分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    anchor_id: int | None = Field(default=None, description='主持人 ID')
    diff_time: str | None = Field(default=None, description='时间范围')


class AddMeetingRecordsModel(MeetingRecordsModel):
    """
    新增会议纪要模型
    """
    pass


class EditMeetingRecordsModel(AddMeetingRecordsModel):
    """
    编辑会议纪要模型
    """
    pass


class DeleteMeetingRecordsModel(BaseModel):
    """
    删除会议纪要模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的会议纪要 ID')
