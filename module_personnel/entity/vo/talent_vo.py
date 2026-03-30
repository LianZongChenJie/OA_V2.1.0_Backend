from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.timeformat import format_timestamp
from pydantic import field_serializer
from typing import Optional,List
class OaTalentBaseModel(BaseModel):
    """入职申请 VO - 用于数据展示"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    id: int = Field(..., description='主键ID')
    name: str = Field(..., description='姓名')
    email: str = Field(..., description='电子邮箱')
    mobile: int = Field(..., description='手机号码')
    mobile_str: str | None = Field(None, description='手机号码字符串')
    sex: int = Field(..., description='性别')
    sex_name: str | None = Field(None, description='性别名称')
    to_did: int = Field(..., description='所属部门')
    to_did_name: str | None = Field(None, description='所属部门名称')
    to_dids: str = Field(..., description='次部门')
    to_dids_list: Optional[List[int]] = Field(None, description='次部门列表')
    thumb: str | None = Field(None, description='头像')
    position_id: int = Field(..., description='职位id')
    position_name_value: str | None = Field(None, description='职位名称')
    type: int = Field(..., description='员工类型')
    type_name: str | None = Field(None, description='员工类型名称')
    job_number: str = Field(..., description='工号')
    birthday: str = Field(..., description='生日')
    pid: int = Field(..., description='上级领导')
    pid_name: str | None = Field(None, description='上级领导姓名')
    work_date: str = Field(..., description='开始工作时间')
    work_location: int = Field(..., description='工作地点')
    work_location_name: str | None = Field(None, description='工作地点名称')
    native_place: str = Field(..., description='籍贯')
    nation: str = Field(..., description='民族')
    home_address: str = Field(..., description='家庭地址')
    current_address: str = Field(..., description='现居地址')
    contact: str = Field(..., description='紧急联系人')
    contact_mobile: str = Field(..., description='紧急联系人电话')
    resident_type: int = Field(..., description='户口性质')
    resident_type_name: str | None = Field(None, description='户口性质名称')
    resident_place: str = Field(..., description='户口所在地')
    graduate_school: str = Field(..., description='毕业学校')
    graduate_day: str = Field(..., description='毕业日期')
    political: int = Field(..., description='政治面貌')
    political_name: str | None = Field(None, description='政治面貌名称')
    marital_status: int = Field(..., description='婚姻状况')
    marital_status_name: str | None = Field(None, description='婚姻状况名称')
    idcard: str = Field(..., description='身份证')
    idcard_masked: str | None = Field(None, description='身份证（脱敏）')
    education: str = Field(..., description='学位')
    speciality: str = Field(..., description='专业')
    bank_account: str = Field(..., description='银行卡号')
    social_account: str = Field(..., description='社保账号')
    salary: int = Field(..., description='期望薪资')
    salary_remark: str = Field(..., description='薪资备注')
    reference_name: str = Field(..., description='推荐人姓名')
    reference_rel: str = Field(..., description='推荐人关系')
    reference_mobile: str = Field(..., description='推荐人联系方式')
    file_ids: str = Field(..., description='档案附件')
    file_ids_list: Optional[List[str]] = Field(None, description='附件列表')
    desc: str | None = Field(None, description='个人简介')
    remark: str | None = Field(None, description='入职评语')
    entry_time: int = Field(..., description='入职时间')
    is_staff: int = Field(..., description='身份类型')
    is_staff_name: str | None = Field(None, description='身份类型名称')
    status: int = Field(..., description='状态')
    status_name: str | None = Field(None, description='状态名称')
    admin_id: int = Field(..., description='创建人')
    did: int = Field(..., description='创建部门')
    create_time: int = Field(..., description='申请时间')
    check_status: int = Field(..., description='审核状态')
    check_status_name: str | None = Field(None, description='审核状态名称')
    check_flow_id: int = Field(..., description='审核流程id')
    check_step_sort: int = Field(..., description='当前审批步骤')
    check_uids: str = Field(..., description='当前审批人ID')
    check_uids_list: Optional[List[int]] = Field(None, description='当前审批人ID列表')
    check_last_uid: str = Field(..., description='上一审批人')
    check_history_uids: str = Field(..., description='历史审批人ID')
    check_history_uids_list: Optional[List[int]] = Field(None, description='历史审批人ID列表')
    check_copy_uids: str = Field(..., description='抄送人ID')
    check_copy_uids_list: Optional[List[int]] = Field(None, description='抄送人ID列表')
    check_time: int = Field(..., description='审核通过时间')
    update_time: int = Field(..., description='更新信息时间')
    talent_id: int = Field(..., description='入职申请id')

    @field_serializer('entry_time')
    def serialize_entry_time(self, value: Optional[int]) -> Optional[str]:
        """序列化入职时间"""
        return format_timestamp(value)

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)
    @field_serializer('check_time')
    def serialize_check_time(self, value: Optional[int]) -> Optional[str]:
        """系列化审核时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)



class OaTalentQueryModel(OaTalentBaseModel):
    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')

class OaTalentPageQueryModel(OaTalentQueryModel):
    """离职分页申请查询VO"""
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')

class OaTalentDetailModel():
    """
    入职详情VO
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    info: OaTalentBaseModel = Field(..., description='入职申请详情')
    records: list[OaFlowRecordBaseModel] = Field(..., description='入职申请审批记录')