from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ResumeAttachmentModel(BaseModel):
    """
    简历附件模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='附件ID')
    file_name: str | None = Field(default=None, description='文件名')
    file_path: str | None = Field(default=None, description='文件路径')
    file_size: int | None = Field(default=None, description='文件大小')
    file_ext: str | None = Field(default=None, description='文件扩展名')
    file_mime: str | None = Field(default=None, description='文件MIME类型')
    sort: int | None = Field(default=0, description='排序')


class ResumeModel(BaseModel):
    """
    简历信息模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='简历ID')
    name: str | None = Field(default=None, description='姓名')
    phone: str | None = Field(default=None, description='手机号码')
    sex: Literal['0', '1', '2'] | None = Field(default='0', description='性别（0男 1女 2未知）')
    idcard: str | None = Field(default=None, description='身份证号')
    email: str | None = Field(default=None, description='邮箱')
    city: str | None = Field(default=None, description='所在城市')
    remark: str | None = Field(default=None, description='备注')
    status: Literal['已投递', '已通过', '未通过', '已入职', '已释放'] | None = Field(
        default='已投递', description='状态：已投递,已通过,未通过,已入职,已释放')
    user_id: int | None = Field(default=None, description='关联用户ID')
    delete_time: int | None = Field(default=0, description='删除时间')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_time: datetime | None = Field(default=None, description='更新时间')
    attachments: List[ResumeAttachmentModel] | None = Field(default=[], description='附件列表')


class ResumePageQueryModel(BaseModel):
    """
    简历分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    name: str | None = Field(default=None, description='姓名')
    phone: str | None = Field(default=None, description='手机号码')
    status: str | None = Field(default=None, description='状态')


class AddResumeModel(ResumeModel):
    """
    新增简历模型
    """
    pass


class EditResumeModel(ResumeModel):
    """
    编辑简历模型
    """
    pass


class DeleteResumeModel(BaseModel):
    """
    删除简历模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的简历ID，多个用逗号分隔')


class InterviewResultModel(BaseModel):
    """
    面试结果模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    resume_id: int = Field(description='简历ID')
    result: Literal['已通过', '未通过'] = Field(description='面试结果')


class ConfirmEntryModel(BaseModel):
    """
    确认入职模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    resume_id: int = Field(description='简历ID')
    dept_id: int = Field(description='部门ID')
    post_id: int = Field(description='岗位ID')
    position_id: int = Field(description='职位ID')
    role_ids: List[int] = Field(description='角色ID列表')
    user_name: str = Field(description='登录账号')
    password: str = Field(description='登录密码')
    nick_name: str | None = Field(default=None, description='用户昵称')
    email: str | None = Field(default=None, description='邮箱')
    is_staff: int | None = Field(default=1, description='身份类型:1企业员工,2劳务派遣,3兼职员工')
    user_type: str | None = Field(default='01', description='用户类型（00系统用户，0未设置,1正式,2试用,3实习）')
    entry_time: int | None = Field(default=None, description='入职日期')
