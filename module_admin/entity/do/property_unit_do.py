from sqlalchemy import BigInteger, Column, Integer, String, Text

from config.database import Base


class SysPropertyUnit(Base):
    """
    资产单位表
    """

    __tablename__ = 'oa_property_unit'
    __table_args__ = {'comment': '资产单位'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='单位 ID')
    title = Column(String(100), nullable=False, server_default="''", comment='单位名称')
    sort = Column(Integer, nullable=True, server_default='0', comment='排序：越大越靠前')
    desc = Column(Text, nullable=True, server_default="''", comment='描述')
    status = Column(Integer, nullable=True, server_default='1', comment='状态：-1 删除 0 禁用 1 启用')
    create_time = Column(BigInteger, nullable=True, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=True, server_default='0', comment='更新时间')
