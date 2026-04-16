from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OaProjectStepRecord(Base):
    """
    项目阶段步骤记录表数据库模型
    """
    __tablename__ = 'oa_project_step_record'
    __table_args__ = {'comment': '项目阶段步骤记录表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    project_id = Column(Integer, nullable=False, default=0, comment='关联项目ID')
    step_id = Column(Integer, nullable=False, default=0, comment='阶段步骤ID')
    check_uid = Column(Integer, nullable=False, default=0, comment='确认人ID')
    check_time = Column(BigInteger, nullable=False, default=0, comment='确认时间')
    status = Column(SmallInteger, nullable=False, default=0, comment='1审核通过2审核拒绝3撤销')
    content = Column(String(500), nullable=False, default='', comment='操作意见')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')