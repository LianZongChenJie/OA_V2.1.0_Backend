# module_project/entity/do/project_user_do.py
from sqlalchemy import Column, Integer, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OaProjectUser(Base):
    """
    项目成员表
    """
    __tablename__ = 'oa_project_user'
    __table_args__ = {'comment': '项目成员表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    uid = Column(Integer, nullable=False, default=0, comment='项目成员id')
    project_id = Column(Integer, nullable=False, comment='关联项目id')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='移除时间')
