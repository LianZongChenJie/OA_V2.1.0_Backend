from sqlalchemy import Column, Integer, BigInteger
from config.database import Base
from sqlalchemy import Index


class OaWorkRecord(Base):
    """汇报工作发送记录表实体类"""

    __tablename__ = 'oa_work_record'
    __table_args__ = (
        Index('idx_work_id', 'work_id'),
        Index('idx_from_uid', 'from_uid'),
        Index('idx_to_uid', 'to_uid'),
        Index('idx_send_time', 'send_time'),
        Index('idx_read_time', 'read_time'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '汇报工作发送记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    work_id = Column(Integer, nullable=False, comment='汇报工作id')
    from_uid = Column(Integer, nullable=False, default=0, comment='发送人id')
    to_uid = Column(Integer, nullable=False, default=0, comment='接收人id')
    send_time = Column(BigInteger, nullable=False, default=0, comment='发送日期')
    read_time = Column(BigInteger, nullable=False, default=0, comment='阅读时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
