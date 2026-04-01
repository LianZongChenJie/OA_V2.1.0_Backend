from sqlalchemy import BigInteger, Column, Integer, String, Text, Float
from sqlalchemy.dialects.mysql import MEDIUMTEXT

from config.database import Base


class CustomerChance(Base):
    """
    客户机会表 ORM 模型
    """
    __tablename__ = 'oa_customer_chance'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='机会 ID')
    title = Column(String(255), nullable=False, default='', comment='销售机会主题')
    cid = Column(Integer, nullable=False, default=0, comment='客户 ID')
    contact_id = Column(Integer, nullable=False, default=0, comment='联系人 ID')
    services_id = Column(Integer, nullable=False, default=0, comment='需求服务 ID')
    stage = Column(Integer, nullable=False, default=0, comment='当前阶段')
    content = Column(MEDIUMTEXT, comment='需求描述')
    discovery_time = Column(BigInteger, nullable=False, default=0, comment='发现时间')
    expected_time = Column(BigInteger, nullable=False, default=0, comment='预计签单时间')
    expected_amount = Column(Float(15, 2), nullable=False, default=0.00, comment='预计签单金额')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    belong_uid = Column(Integer, nullable=False, default=0, comment='所属人')
    assist_ids = Column(String(500), nullable=False, default='', comment='协助人员，如:1,2,3')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
