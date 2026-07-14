"""
简历信息表实体类
"""
from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text


class OaResume(Base):
    """简历信息表实体类"""

    __tablename__ = 'oa_resume'
    __table_args__ = {'comment': '简历信息表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    resume_uuid = Column(String(64), nullable=False, unique=True, default='', comment='简历唯一UUID')
    file_name = Column(String(256), nullable=False, default='', comment='原始文件名')
    name = Column(String(128), nullable=False, default='', comment='姓名')
    gender = Column(String(16), nullable=False, default='', comment='性别')
    age = Column(Integer, nullable=False, default=0, comment='年龄')
    birth_date = Column(String(32), nullable=False, default='', comment='出生日期')
    phone = Column(String(64), nullable=False, default='', comment='联系电话')
    email = Column(String(128), nullable=False, default='', comment='邮箱')
    education = Column(String(64), nullable=False, default='', comment='学历')
    major = Column(String(128), nullable=False, default='', comment='专业')
    school = Column(String(128), nullable=False, default='', comment='毕业院校')
    graduation_date = Column(String(32), nullable=False, default='', comment='毕业时间')
    work_years = Column(Integer, nullable=False, default=0, comment='工作年限')
    current_company = Column(String(256), nullable=False, default='', comment='当前公司')
    current_position = Column(String(128), nullable=False, default='', comment='当前职位')
    id_card_number = Column(String(18), nullable=False, default='', comment='身份证号')
    id_card_address = Column(String(500), nullable=False, default='', comment='身份证地址')
    degree = Column(String(32), nullable=False, default='', comment='学位（学士/硕士/博士）')
    school_system = Column(String(16), nullable=False, default='', comment='学制')
    study_form = Column(String(32), nullable=False, default='', comment='学习形式（全日制/非全日制等）')
    technical_skills = Column(Text, nullable=False, default='', comment='技术技能（JSON数组）')
    certifications = Column(Text, nullable=False, default='', comment='证书详情（JSON数组[{name,number,issue_date,issuer}]）')
    tags = Column(Text, nullable=False, default='', comment='标签（逗号分隔）')
    full_text = Column(Text, nullable=False, default='', comment='简历全文')
    parse_time = Column(BigInteger, nullable=False, default=0, comment='解析耗时(ms)')
    status = Column(SmallInteger, nullable=False, default=1, comment='状态:0删除,1正常')
    source_type = Column(SmallInteger, nullable=False, default=1, comment='来源类型:1独立简历,2投标文件简历')
    source_id = Column(Integer, nullable=False, default=0, comment='来源ID（投标文件ID）')
    source_name = Column(String(256), nullable=False, default='', comment='来源名称')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='修改时间')

    def __repr__(self) -> str:
        return f"<OaResume(id={self.id}, name='{self.name}', education='{self.education}')>"


class OaResumeWork(Base):
    """简历工作经历表实体类"""

    __tablename__ = 'oa_resume_work'
    __table_args__ = {'comment': '简历工作经历表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    resume_id = Column(Integer, nullable=False, default=0, comment='简历ID')
    company = Column(String(256), nullable=False, default='', comment='公司名称')
    position = Column(String(128), nullable=False, default='', comment='职位')
    start_date = Column(String(32), nullable=False, default='', comment='开始时间')
    end_date = Column(String(32), nullable=False, default='', comment='结束时间')
    description = Column(Text, nullable=False, default='', comment='工作描述')
    sort = Column(Integer, nullable=False, default=0, comment='排序')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')

    def __repr__(self) -> str:
        return f"<OaResumeWork(id={self.id}, company='{self.company}', position='{self.position}')>"


class OaResumeProject(Base):
    """简历项目经验表实体类"""

    __tablename__ = 'oa_resume_project'
    __table_args__ = {'comment': '简历项目经验表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    resume_id = Column(Integer, nullable=False, default=0, comment='简历ID')
    project_name = Column(String(256), nullable=False, default='', comment='项目名称')
    role = Column(String(128), nullable=False, default='', comment='项目角色')
    start_date = Column(String(32), nullable=False, default='', comment='开始时间')
    end_date = Column(String(32), nullable=False, default='', comment='结束时间')
    description = Column(Text, nullable=False, default='', comment='项目描述')
    technologies = Column(Text, nullable=False, default='', comment='使用技术（JSON数组）')
    sort = Column(Integer, nullable=False, default=0, comment='排序')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')

    def __repr__(self) -> str:
        return f"<OaResumeProject(id={self.id}, project_name='{self.project_name}', role='{self.role}')>"
