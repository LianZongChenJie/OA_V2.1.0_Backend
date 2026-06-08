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
    remark = Column(Text, nullable=True, server_default="''", comment='备注')
    status = Column(String(20), nullable=False, server_default='已投递', comment='状态：已投递,已通过,未通过,已入职,已释放')
    # 入职后关联的用户ID（为空表示未入职）
    user_id = Column(BigInteger, nullable=True, comment='关联用户ID')
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
