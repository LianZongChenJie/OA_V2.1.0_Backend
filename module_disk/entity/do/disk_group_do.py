"""
网盘分享空间表实体类
"""
from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger


class OaDiskGroup(Base):
    """网盘分享空间表实体类"""

    __tablename__ = 'oa_disk_group'
    __table_args__ = {'comment': '网盘分享空间表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    title = Column(String(255), nullable=False, default='', comment='分享空间名称')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    director_uids = Column(String(500), nullable=False, default='', comment='管理人员')
    group_uids = Column(String(500), nullable=False, default='', comment='群组成员')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def __repr__(self) -> str:
        return f"<OaDiskGroup(id={self.id}, title='{self.title}')>"
