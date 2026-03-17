from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from config.database import Base


class SysCareCate(Base):
    """
    关怀项目表
    """

    __tablename__ = 'oa_care_cate'
    __table_args__ = {'comment': '关怀项目'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='关怀项目 ID')
    title = Column(String(100), nullable=False, server_default="''", comment='关怀项目名称')
    status = Column(Integer, nullable=True, server_default='1', comment='状态：-1 删除 0 禁用 1 启用')
    create_time = Column(BigInteger, nullable=True, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=True, server_default='0', comment='更新时间')

