from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from config.database import Base


class SysBasicUser(Base):
    """
    人事模块常规数据表
    """

    __tablename__ = 'oa_basic_user'
    __table_args__ = {'comment': '人事模块常规数据'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='ID')
    types = Column(String(100), nullable=False, server_default="''", comment='数据类型:1 职务，2 职级，3 看后期增加')
    title = Column(String(100), nullable=False, server_default="''", comment='名称')
    status = Column(Integer, nullable=True, server_default='1', comment='状态：-1 删除 0 禁用 1 启用')
    create_time = Column(BigInteger, nullable=True, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=True, server_default='0', comment='更新时间')

