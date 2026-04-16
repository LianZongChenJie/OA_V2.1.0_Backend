from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OaProjectStep(Base):
    """
    项目阶段步骤表数据库模型
    """
    __tablename__ = 'oa_project_step'
    __table_args__ = {'comment': '项目阶段步骤表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    project_id = Column(Integer, nullable=False, default=0, comment='关联ID')
    title = Column(String(255), nullable=False, default='', comment='阶段名称')
    director_uid = Column(Integer, nullable=False, default=0, comment='阶段负责人ID')
    uids = Column(String(500), nullable=False, default='', comment='阶段成员ID (使用逗号隔开) 1,2,3')
    sort = Column(SmallInteger, nullable=False, default=0, comment='排序ID')
    is_current = Column(SmallInteger, nullable=False, default=0, comment='是否是当前阶段')
    start_time = Column(BigInteger, nullable=False, default=0, comment='开始时间')
    end_time = Column(BigInteger, nullable=False, default=0, comment='结束时间')
    remark = Column(String(500), nullable=False, default='', comment='阶段说明')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='修改时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')