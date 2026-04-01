# 1. 创建 DO 文件：module_admin/entity/do/customer_trace_do.py
from sqlalchemy import BigInteger, Column, Integer, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT

from config.database import Base


class CustomerTrace(Base):
    """
    客户跟进记录表 ORM 模型
    """
    __tablename__ = 'oa_customer_trace'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='跟进记录 ID')
    cid = Column(Integer, nullable=False, default=0, comment='客户 ID')
    contact_id = Column(Integer, nullable=False, default=0, comment='联系人 id')
    chance_id = Column(Integer, nullable=False, default=0, comment='销售机会 id')
    types = Column(Integer, nullable=False, default=0, comment='跟进方式')
    stage = Column(Integer, nullable=False, default=0, comment='当前阶段')
    content = Column(MEDIUMTEXT, comment='跟进内容')
    follow_time = Column(BigInteger, nullable=False, default=0, comment='跟进时间')
    next_time = Column(BigInteger, nullable=False, default=0, comment='下次跟进时间')
    file_ids = Column(String(500), nullable=False, default='', comment='附件 ids,如:1,2,3')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

