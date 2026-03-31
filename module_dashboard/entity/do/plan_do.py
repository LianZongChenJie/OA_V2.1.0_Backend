from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text
from config.database import Base
from sqlalchemy import Index

class OaPlan(Base):
    """日程安排实体类"""

    __tablename__ = 'oa_plan'
    __table_args__ = (
        Index('idx_admin_id', 'admin_id'),
        Index('idx_did', 'did'),
        Index('idx_start_time', 'start_time'),
        Index('idx_end_time', 'end_time'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '日程安排'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    title = Column(String(255), nullable=False, default='', comment='工作安排主题')
    type = Column(String(100), nullable=False, default='', comment='日程优先级')
    cid = Column(Integer, nullable=False, default=0, comment='预设字段:关联工作内容类型ID')
    cmid = Column(Integer, nullable=False, default=0, comment='预设字段:关联客户ID')
    ptid = Column(Integer, nullable=False, default=0, comment='预设字段:关联项目ID')
    admin_id = Column(Integer, nullable=False, default=0, comment='关联创建员工ID')
    did = Column(Integer, nullable=False, default=0, comment='所属部门')
    start_time = Column(BigInteger, nullable=False, default=0, comment='开始时间')
    end_time = Column(BigInteger, nullable=False, default=0, comment='结束时间')
    remind_type = Column(Integer, nullable=False, default=0, comment='提醒类型')
    remind_time = Column(BigInteger, nullable=False, default=0, comment='提醒时间')
    remark = Column(Text, nullable=False, comment='描述')
    file_ids = Column(String(500), nullable=False, default='', comment='相关附件')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}