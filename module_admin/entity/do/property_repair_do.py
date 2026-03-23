from sqlalchemy import Column, Integer, String, BigInteger, DECIMAL, Text
from config.database import Base

class OaPropertyRepair(Base):
    """
    資產維修記錄表
    """
    __tablename__ = 'oa_property_repair'
    __table_args__ = {'comment': '資產維修記錄表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    property_id = Column(Integer, nullable=False, server_default='0', comment='資產 ID')
    repair_time = Column(BigInteger, nullable=False, server_default='0', comment='維修日期')
    cost = Column(DECIMAL(precision=15, scale=2), nullable=False, server_default='0.00', comment='維修費用')
    content = Column(Text, nullable=True, comment='維修原因')
    file_ids = Column(String(255), nullable=False, server_default='', comment='附件 ids')
    director_id = Column(Integer, nullable=False, server_default='0', comment='跟進人 ID')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='創建人')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='創建時間')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新時間')
    delete_time = Column(BigInteger, nullable=True, default=0, comment='刪除時間')
