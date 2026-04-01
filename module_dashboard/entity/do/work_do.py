from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text, DECIMAL
from config.database import Base
from sqlalchemy import Index

class OaWork(Base):
    """汇报工作表实体类"""

    __tablename__ = 'oa_work'
    __table_args__ = (
        Index('idx_admin_id', 'admin_id'),
        Index('idx_create_time', 'create_time'),
        Index('idx_start_date', 'start_date'),
        Index('idx_end_date', 'end_date'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '汇报工作表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    types = Column(SmallInteger, nullable=True, default=0, comment='类型：1 日报 2周报 3月报')
    start_date = Column(BigInteger, nullable=False, default=0, comment='开始日期')
    end_date = Column(BigInteger, nullable=False, default=0, comment='结束日期')
    to_uids = Column(Text, nullable=True, comment='接受人员ID')
    works = Column(Text, nullable=True, comment='汇报工作内容')
    plans = Column(Text, nullable=True, comment='计划工作内容')
    remark = Column(Text, nullable=True, comment='其他事项')
    file_ids = Column(String(500), nullable=False, default='', comment='附件，如:1,2,3')
    send_time = Column(BigInteger, nullable=False, default=0, comment='发送时间')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人id')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}