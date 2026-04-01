from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text, DECIMAL
from config.database import Base
from sqlalchemy import Index
class OaSchedule(Base):
    """工作记录实体类"""

    __tablename__ = 'oa_schedule'
    __table_args__ = (
        Index('idx_admin_id', 'admin_id'),
        Index('idx_did', 'did'),
        Index('idx_start_time', 'start_time'),
        Index('idx_end_time', 'end_time'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '工作记录'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    title = Column(String(255), nullable=False, default='', comment='工作记录主题')
    cid = Column(Integer, nullable=False, default=1, comment='预设字段:关联工作内容类型ID')
    cmid = Column(Integer, nullable=False, default=0, comment='预设字段:关联客户ID')
    ptid = Column(Integer, nullable=False, default=0, comment='预设字段:关联项目ID')
    tid = Column(Integer, nullable=False, default=0, comment='预设字段:关联任务ID')
    admin_id = Column(Integer, nullable=False, default=0, comment='关联创建员工ID')
    did = Column(Integer, nullable=False, default=0, comment='所属部门')
    start_time = Column(BigInteger, nullable=False, default=0, comment='开始时间')
    end_time = Column(BigInteger, nullable=False, default=0, comment='结束时间')
    labor_time = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='工时')
    labor_type = Column(SmallInteger, nullable=False, default=0, comment='工作类型:1案头2外勤')
    remark = Column(Text, nullable=False, comment='描述')
    file_ids = Column(String(500), nullable=False, default='', comment='相关附件')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
