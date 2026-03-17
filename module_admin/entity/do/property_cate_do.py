from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text

from config.database import Base


class SysPropertyCate(Base):
    """
    资产分类表
    """

    __tablename__ = 'oa_property_cate'
    __table_args__ = {'comment': '资产分类'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='分类 ID')
    title = Column(String(100), nullable=False, server_default="''", comment='分类名称')
    pid = Column(Integer, nullable=True, server_default='0', comment='父分类 ID')
    sort = Column(Integer, nullable=True, server_default='0', comment='排序：越大越靠前')
    desc = Column(Text, nullable=True, server_default="''", comment='分类说明')
    status = Column(Integer, nullable=True, server_default='1', comment='状态：-1 删除 0 禁用 1 启用')
    admin_id = Column(Integer, nullable=True, server_default='0', comment='创建人')
    create_time = Column(BigInteger, nullable=True, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=True, server_default='0', comment='更新时间')

