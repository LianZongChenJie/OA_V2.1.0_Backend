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
    city_id: str | None = Field(default=None, description='城市ID')
    remark: str | None = Field(default=None, description='备注')
    status: Literal['1', '2', '3', '4', '5'] | None = Field(
        default=None, description='状态：1已投递,2已通过,3未通过,4已入职,5已释放')
    user_id: int | None = Field(default=None, description='关联用户ID')
    # 部门岗位相关
    dept_id: int | None = Field(default=None, description='归属部门ID')
    dept_name: str | None = Field(default=None, description='归属部门名称')
    post_id: int | None = Field(default=None, description='岗位ID')
    post_name: str | None = Field(default=None, description='岗位名称')
    # 推荐相关
    recommender_id: int | None = Field(default=None, description='推荐人ID')
    recommender_name: str | None = Field(default=None, description='推荐人姓名')
    recommend_time: datetime | None = Field(default=None, description='推荐时间')
    recommend_project_id: int | None = Field(default=None, description='推荐项目ID')
    recommend_project_name: str | None = Field(default=None, description='推荐项目名称')
    recommend_customer_id: int | None = Field(default=None, description='推荐客户ID')
    recommend_customer_name: str | None = Field(default=None, description='推荐客户名称')
    # 学历相关
    education: str | None = Field(default=None, description='最高学历：初中,高中,专科,本科,硕士,博士')
    graduate_school: str | None = Field(default=None, description='毕业院校')
    graduate_year: int | None = Field(default=None, description='毕业年份')
    age: int | None = Field(default=None, description='年龄')
    # 入场相关
    is_entry: int | None = Field(default=0, description='是否入场：0否，1是')
    entry_project_id: int | None = Field(default=None, description='入场项目ID')
    entry_project_name: str | None = Field(default=None, description='入场项目名称')
    entry_time: datetime | None = Field(default=None, description='入场时间')
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
    # 新增筛选条件
    age_min: int | None = Field(default=None, description='最小年龄')
    age_max: int | None = Field(default=None, description='最大年龄')
    education: str | None = Field(default=None, description='学历')
    graduate_year_min: int | None = Field(default=None, description='毕业年限最小值')
    graduate_year_max: int | None = Field(default=None, description='毕业年限最大值')
    is_entry: int | None = Field(default=None, description='是否入场：0否，1是')
    recommender_id: int | None = Field(default=None, description='推荐人ID')
    # 新增筛选条件
    age_min: int | None = Field(default=None, description='最小年龄')
    age_max: int | None = Field(default=None, description='最大年龄')
    education: str | None = Field(default=None, description='学历')
    graduate_year_min: int | None = Field(default=None, description='毕业年限最小值')
    graduate_year_max: int | None = Field(default=None, description='毕业年限最大值')
    is_entry: int | None = Field(default=None, description='是否入场：0否，1是')
    recommender_id: int | None = Field(default=None, description='推荐人ID')


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


class ReleaseResumeModel(BaseModel):
    """
    释放简历模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    resume_id: int = Field(description='简历ID')
    status: str = Field(default='5', description='释放后的状态，默认5（已释放）')


class InterviewResultModel(BaseModel):
    """
    面试结果模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    resume_id: int = Field(description='简历ID')
    status: int = Field(description='面试结果：1已通过，2未通过')


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
    entry_time: str | None = Field(default=None, description='入职日期')


class ResumeRecommendModel(BaseModel):
    """
    简历推荐模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='推荐记录ID')
    resume_id: int = Field(description='简历ID')
    project_id: int | None = Field(default=None, description='推荐项目ID')
    project_name: str | None = Field(default=None, description='项目名称')
    customer_id: int | None = Field(default=None, description='推荐客户ID')
    customer_name: str | None = Field(default=None, description='推荐客户名称')
    recommender_id: int | None = Field(default=None, description='推荐人ID')
    recommender_name: str | None = Field(default=None, description='推荐人姓名')
    recommend_time: datetime | None = Field(default=None, description='推荐时间')
    status: str | None = Field(default='推荐中', description='推荐状态')
    remark: str | None = Field(default=None, description='备注')
    email_url: str | None = Field(default=None, description='收件人邮箱地址')
    file_path: str | None = Field(default=None, description='附件文件路径')


class ResumeEmailTemplateModel(BaseModel):
    """
    邮件模板模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='模板ID')
    template_name: str = Field(description='模板名称')
    template_content: str = Field(description='模板内容')
    subject: str | None = Field(default=None, description='邮件主题')
    is_default: int | None = Field(default=0, description='是否默认：0否，1是')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_time: datetime | None = Field(default=None, description='更新时间')


class EmailTemplatePageQueryModel(BaseModel):
    """
    邮件模板分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    page_num: int | None = Field(default=1, description='页码')
    page_size: int | None = Field(default=10, description='每页数量')


class AddEmailTemplateModel(ResumeEmailTemplateModel):
    """
    新增邮件模板模型
    """
    pass


class EditEmailTemplateModel(ResumeEmailTemplateModel):
    """
    编辑邮件模板模型
    """
    pass


class DeleteEmailTemplateModel(BaseModel):
    """
    删除邮件模板模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的模板ID，多个用逗号分隔')


class ResumeUploadParseModel(BaseModel):
    """
    简历上传解析模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    file_path: str = Field(description='文件路径')
    file_name: str = Field(description='文件名')


class EntryProjectModel(BaseModel):
    """
    入场项目模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    resume_id: int = Field(description='简历ID')
    project_id: int = Field(description='项目ID')


class ResumeRecommendPageQueryModel(BaseModel):
    """
    简历推荐记录分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    resume_id: int | None = Field(default=None, description='简历ID')
    project_name: str | None = Field(default=None, description='项目名称')
    recommender_name: str | None = Field(default=None, description='推荐人姓名')


class ResumeRecommendPageQueryModel(BaseModel):
    """
    简历推荐记录分页查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    resume_id: int | None = Field(default=None, description='简历ID')
    project_name: str | None = Field(default=None, description='项目名称')
    recommender_name: str | None = Field(default=None, description='推荐人姓名')


class ResumeEmailTemplateModel(BaseModel):
    """
    邮件模板模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='模板ID')
    template_name: str = Field(description='模板名称')
    template_content: str = Field(description='模板内容')
    subject: str | None = Field(default=None, description='邮件主题')
    is_default: int | None = Field(default=0, description='是否默认：0否，1是')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_time: datetime | None = Field(default=None, description='更新时间')


class AddEmailTemplateModel(ResumeEmailTemplateModel):
    """
    新增邮件模板模型
    """
    pass


class EditEmailTemplateModel(ResumeEmailTemplateModel):
    """
    编辑邮件模板模型
    """
    pass


class DeleteEmailTemplateModel(BaseModel):
    """
    删除邮件模板模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的模板ID，多个用逗号分隔')


class ResumeUploadParseModel(BaseModel):
    """
    简历上传解析模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    file_path: str = Field(description='文件路径')
    file_name: str = Field(description='文件名')


class EntryProjectModel(BaseModel):
    """
    入场项目模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    resume_id: int = Field(description='简历ID')
    project_id: int = Field(description='项目ID')


class ResumeEmailTemplateModel(BaseModel):
    """
    邮件模板模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='模板ID')
    template_name: str = Field(description='模板名称')
    template_content: str = Field(description='模板内容')
    subject: str | None = Field(default=None, description='邮件主题')
    is_default: int | None = Field(default=0, description='是否默认：0否，1是')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_time: datetime | None = Field(default=None, description='更新时间')


class AddEmailTemplateModel(ResumeEmailTemplateModel):
    """
    新增邮件模板模型
    """
    pass


class EditEmailTemplateModel(ResumeEmailTemplateModel):
    """
    编辑邮件模板模型
    """
    pass


class DeleteEmailTemplateModel(BaseModel):
    """
    删除邮件模板模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的模板ID，多个用逗号分隔')


class ResumeUploadParseModel(BaseModel):
    """
    简历上传解析模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    file_path: str = Field(description='文件路径')
    file_name: str = Field(description='文件名')


class EntryProjectModel(BaseModel):
    """
    入场项目模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    resume_id: int = Field(description='简历ID')
    project_id: int = Field(description='项目ID')