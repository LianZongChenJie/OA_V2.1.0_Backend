from datetime import datetime

from sqlalchemy import BigInteger, Column, Integer, String

from config.database import Base


class SysNoteCate(Base):
    """
    公告分类表
    """

    __tablename__ = 'oa_note_cate'
    __table_args__ = {'comment': '公告分类'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='公告分类 ID')
    pid = Column(Integer, nullable=False, server_default='0', comment='父类 ID')
    sort = Column(Integer, nullable=False, server_default='0', comment='排序')
    title = Column(String(50), nullable=False, server_default="''", comment='标题')
    status = Column(Integer, nullable=False, server_default='1', comment='1 可用 -1 禁用')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='添加时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='修改时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')

