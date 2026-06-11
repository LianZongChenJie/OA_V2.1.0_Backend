from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime

from config.database import Base


class ResumeInfo(Base):
    """
    简历信息表
    """
    __tablename__ = 'resume_info'
    __table_args__ = {'comment': '简历信息表'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='简历ID')
    name = Column(String(50), nullable=False, comment='姓名')
    phone = Column(String(11), nullable=False, comment='手机号码')
    sex = Column(String(1), nullable=True, server_default='0', comment='性别（0男 1女 2未知）')
    idcard = Column(String(18), nullable=True, server_default="''", comment='身份证号')
    email = Column(String(50), nullable=True, server_default="''", comment='邮箱')
    city = Column(String(50), nullable=True, server_default="''", comment='所在城市')
    city_id = Column(String(50), nullable=True, server_default="''", comment='城市ID')
    remark = Column(Text, nullable=True, server_default="''", comment='备注')
    status = Column(String(20), nullable=False, server_default='1', comment='状态：1已投递,2已通过,3未通过,4已入职,5已释放')
    # 入职后关联的用户ID（为空表示未入职）
    user_id = Column(BigInteger, nullable=True, comment='关联用户ID')
    # 推荐相关字段
    recommender_id = Column(BigInteger, nullable=True, comment='推荐人ID')
    recommender_name = Column(String(50), nullable=True, server_default="''", comment='推荐人姓名')
    recommend_time = Column(DateTime, nullable=True, comment='推荐时间')
    recommend_project_id = Column(Integer, nullable=True, comment='推荐项目ID')
    recommend_customer_id = Column(Integer, nullable=True, comment='推荐客户ID')
    recommend_customer_name = Column(String(255), nullable=True, server_default="''", comment='推荐客户名称')
    # 学历相关字段
    education = Column(String(20), nullable=True, server_default="''", comment='最高学历：初中,高中,专科,本科,硕士,博士')
    graduate_school = Column(String(100), nullable=True, server_default="''", comment='毕业院校')
    graduate_year = Column(Integer, nullable=True, comment='毕业年份')
    age = Column(Integer, nullable=True, comment='年龄')
    # 入职相关
    is_entry = Column(Integer, nullable=True, server_default='0', comment='是否入场：0否，1是')
    entry_project_id = Column(Integer, nullable=True, comment='入场项目ID')
    entry_project_name = Column(String(255), nullable=True, server_default="''", comment='入场项目名称')
    entry_time = Column(DateTime, nullable=True, comment='入场时间')
    delete_time = Column(BigInteger, nullable=True, server_default='0', comment='删除时间')
    create_time = Column(DateTime, nullable=True, comment='创建时间', default=datetime.now())
    update_time = Column(DateTime, nullable=True, comment='更新时间', default=datetime.now())


class ResumeAttachment(Base):
    """
    简历附件表
    """
    __tablename__ = 'resume_attachment'
    __table_args__ = {'comment': '简历附件表'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='附件ID')
    resume_id = Column(Integer, nullable=False, comment='简历ID')
    file_name = Column(String(255), nullable=False, comment='文件名')
    file_path = Column(String(255), nullable=False, comment='文件路径')
    file_size = Column(BigInteger, nullable=True, comment='文件大小')
    file_ext = Column(String(20), nullable=True, comment='文件扩展名')
    file_mime = Column(String(100), nullable=True, comment='文件MIME类型')
    sort = Column(Integer, nullable=True, server_default='0', comment='排序')
    delete_time = Column(BigInteger, nullable=True, server_default='0', comment='删除时间')


class ResumeRecommend(Base):
    """
    简历推荐记录表
    """
    __tablename__ = 'resume_recommend'
    __table_args__ = {'comment': '简历推荐记录表'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='推荐记录ID')
    resume_id = Column(Integer, nullable=False, comment='简历ID')
    project_id = Column(Integer, nullable=True, comment='推荐项目ID')
    project_name = Column(String(255), nullable=True, comment='项目名称')
    customer_id = Column(Integer, nullable=True, comment='推荐客户ID')
    customer_name = Column(String(255), nullable=True, comment='推荐客户名称')
    recommender_id = Column(BigInteger, nullable=False, comment='推荐人ID')
    recommender_name = Column(String(50), nullable=True, comment='推荐人姓名')
    recommend_time = Column(DateTime, nullable=True, comment='推荐时间', default=datetime.now())
    status = Column(String(20), nullable=False, server_default='推荐中', comment='推荐状态：推荐中,已录用,未录用')
    remark = Column(Text, nullable=True, comment='备注')
    delete_time = Column(BigInteger, nullable=True, server_default='0', comment='删除时间')


class ResumeEmailTemplate(Base):
    """
    简历邮件模板表
    """
    __tablename__ = 'resume_email_template'
    __table_args__ = {'comment': '简历邮件模板表'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='模板ID')
    template_name = Column(String(100), nullable=False, comment='模板名称')
    template_content = Column(Text, nullable=False, comment='模板内容')
    subject = Column(String(200), nullable=True, comment='邮件主题')
    is_default = Column(Integer, nullable=True, server_default='0', comment='是否默认：0否，1是')
    create_time = Column(DateTime, nullable=True, comment='创建时间', default=datetime.now())
    update_time = Column(DateTime, nullable=True, comment='更新时间', default=datetime.now())