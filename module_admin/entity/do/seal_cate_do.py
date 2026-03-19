from datetime import datetime

from sqlalchemy import BigInteger, Column, Integer, String, Text

from config.database import Base


class SysSealCate(Base):
    """
    印章类别表
    """

    __tablename__ = 'oa_seal_cate'
    __table_args__ = {'comment': '印章类型'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='印章类别 ID')
    title = Column(String(100), nullable=False, server_default="''", comment='印章名称')
    dids = Column(String(255), nullable=True, server_default="''", comment='应用部门')
    keep_uid = Column(Integer, nullable=True, server_default='0', comment='保管人')
    status = Column(Integer, nullable=True, server_default='1', comment='状态：-1 删除 0 禁用 1 启用')
    remark = Column(Text, nullable=True, server_default="''", comment='用途简述')
    create_time = Column(BigInteger, nullable=True, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=True, server_default='0', comment='更新时间')

