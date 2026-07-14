"""
简历知识库相关 Pydantic 模型
"""
import json
from typing import Any, List
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class CertificationModel(BaseModel):
    """证书详情模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    name: str | None = Field(default='', description='证书名称')
    number: str | None = Field(default='', description='证书编号')
    issue_date: str | None = Field(default='', description='发证日期')
    issuer: str | None = Field(default='', description='发证机构')


class ResumeWorkExperienceModel(BaseModel):
    """工作经历模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    company: str | None = Field(default='', description='公司名称')
    position: str | None = Field(default='', description='职位')
    start_date: str | None = Field(default='', description='开始时间')
    end_date: str | None = Field(default='', description='结束时间')
    description: str | None = Field(default='', description='工作描述')


class ResumeProjectExperienceModel(BaseModel):
    """项目经验模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    project_name: str | None = Field(default='', description='项目名称')
    role: str | None = Field(default='', description='项目角色')
    start_date: str | None = Field(default='', description='开始时间')
    end_date: str | None = Field(default='', description='结束时间')
    description: str | None = Field(default='', description='项目描述')
    technologies: List[str] | None = Field(default=[], description='使用技术')


class ResumeModel(BaseModel):
    """简历信息模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    @model_validator(mode='before')
    @classmethod
    def normalize_list_fields(cls, data: Any) -> Any:
        """
        兼容数据库ORM对象：
        - technical_skills / certifications 在DB中是 JSON字符串，需自动反序列化
        - tags 在DB中是逗号分隔字符串，需转列表
        """
        if hasattr(data, '__dict__'):
            # SQLAlchemy ORM 对象
            d = {}
            for key in ['id', 'resume_uuid', 'file_name', 'name', 'gender', 'age',
                        'birth_date', 'phone', 'email', 'education', 'major', 'school',
                        'graduation_date', 'work_years', 'current_company', 'current_position',
                        'id_card_number', 'id_card_address', 'degree', 'school_system', 'study_form',
                        'technical_skills', 'certifications', 'tags', 'full_text',
                        'parse_time', 'status', 'admin_id', 'create_time', 'update_time',
                        'source_type', 'source_id', 'source_name']:
                if hasattr(data, key):
                    d[key] = getattr(data, key)
            # JSON字符串字段反序列化
            for field in ['technical_skills', 'certifications']:
                val = d.get(field, '')
                if isinstance(val, str):
                    try:
                        parsed = json.loads(val) if val else []
                        # certifications 可能存的是旧格式字符串数组，兼容处理
                        if field == 'certifications' and parsed and isinstance(parsed, list):
                            if all(isinstance(item, str) for item in parsed):
                                # 旧格式：字符串数组 → 转为新格式对象数组
                                parsed = [{'name': item, 'number': '', 'issue_date': '', 'issuer': ''} for item in parsed]
                        d[field] = parsed
                    except (json.JSONDecodeError, TypeError):
                        d[field] = []
            # tags 逗号分隔字符串转列表
            val = d.get('tags', '')
            if isinstance(val, str):
                d['tags'] = [t.strip() for t in val.split(',') if t.strip()]
            return d
        return data

    id: int | None = Field(default=0, description='ID')
    resume_uuid: str | None = Field(default='', description='简历唯一UUID')
    file_name: str | None = Field(default='', description='原始文件名')
    name: str | None = Field(default='', description='姓名')
    gender: str | None = Field(default='', description='性别')
    age: int | None = Field(default=0, description='年龄')
    birth_date: str | None = Field(default='', description='出生日期')
    phone: str | None = Field(default='', description='联系电话')
    email: str | None = Field(default='', description='邮箱')
    education: str | None = Field(default='', description='学历')
    major: str | None = Field(default='', description='专业')
    school: str | None = Field(default='', description='毕业院校')
    graduation_date: str | None = Field(default='', description='毕业时间')
    work_years: int | None = Field(default=0, description='工作年限')
    current_company: str | None = Field(default='', description='当前公司')
    current_position: str | None = Field(default='', description='当前职位')
    id_card_number: str | None = Field(default='', description='身份证号')
    id_card_address: str | None = Field(default='', description='身份证地址')
    degree: str | None = Field(default='', description='学位（学士/硕士/博士）')
    school_system: str | None = Field(default='', description='学制')
    study_form: str | None = Field(default='', description='学习形式（全日制/非全日制等）')
    technical_skills: List[str] | None = Field(default=[], description='技术技能')
    certifications: List[CertificationModel] | None = Field(default=[], description='证书详情')
    tags: List[str] | None = Field(default=[], description='标签')
    full_text: str | None = Field(default='', description='简历全文')
    parse_time: int | None = Field(default=0, description='解析耗时(ms)')
    work_experiences: List[ResumeWorkExperienceModel] | None = Field(default=[], description='工作经历')
    project_experiences: List[ResumeProjectExperienceModel] | None = Field(default=[], description='项目经验')
    admin_id: int | None = Field(default=0, description='创建人')
    create_time: int | None = Field(default=0, description='创建时间')
    update_time: int | None = Field(default=0, description='修改时间')


class ResumePageQueryModel(BaseModel):
    """简历分页查询模型"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    # 学历筛选（支持模糊匹配）
    education: str | None = Field(default=None, description='学历筛选')
    # 姓名精确/模糊匹配
    name: str | None = Field(default=None, description='姓名关键词')
    # 年龄范围筛选
    min_age: int | None = Field(default=None, description='最小年龄')
    max_age: int | None = Field(default=None, description='最大年龄')
    # 技能关键词筛选
    skill: str | None = Field(default=None, description='技能关键词')
    # 专业关键词筛选
    major: str | None = Field(default=None, description='专业关键词')
    # 公司名称筛选
    company: str | None = Field(default=None, description='公司关键词')
    # 职位关键词筛选
    position: str | None = Field(default=None, description='职位关键词')
    # 项目经验关键词筛选
    project_keyword: str | None = Field(default=None, description='项目经验关键词')
    # 全文关键词
    keyword: str | None = Field(default=None, description='全文关键词')


class ResumeUploadResultModel(BaseModel):
    """简历上传结果模型"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    success: bool = Field(default=True, description='是否成功')
    message: str = Field(default='', description='结果消息')
    resume_id: int | None = Field(default=0, description='简历ID')
    resume_uuid: str | None = Field(default='', description='简历UUID')
    file_name: str | None = Field(default='', description='文件名')
    processing_time: int | None = Field(default=0, description='处理耗时(ms)')
    name: str | None = Field(default='', description='姓名')
    education: str | None = Field(default='', description='学历')
    major: str | None = Field(default='', description='专业')
    age: int | None = Field(default=0, description='年龄')
    work_years: int | None = Field(default=0, description='工作年限')
    technical_skills: List[str] | None = Field(default=[], description='技术技能')
    tags: List[str] | None = Field(default=[], description='标签')


class ResumeSearchResultModel(BaseModel):
    """简历搜索结果模型"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    success: bool = Field(default=True, description='是否成功')
    message: str | None = Field(default='', description='结果消息')
    total: int = Field(default=0, description='总数')
    resumes: List[ResumeModel] | None = Field(default=[], description='简历列表')


class ResumeChatRequestModel(BaseModel):
    """简历智能问答请求模型"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: str | None = Field(default=None, description='会话ID')
    model_id: int = Field(description='模型ID')
    message: str = Field(description='用户问题')
    top_k: int | None = Field(default=5, description='检索简历数量')
    stream: bool | None = Field(default=True, description='是否流式返回')


class ResumeChatRelatedResumeModel(BaseModel):
    """关联简历模型"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int | None = Field(default=0, description='简历ID')
    name: str | None = Field(default='', description='姓名')
    position: str | None = Field(default='', description='应聘职位')
    education: str | None = Field(default='', description='学历')
    work_years: int | None = Field(default=0, description='工作年限')
    school: str | None = Field(default='', description='毕业院校')
    skills: List[str] | None = Field(default=[], description='技能')
