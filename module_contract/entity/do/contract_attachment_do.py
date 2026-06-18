from datetime import datetime
from sqlalchemy import BigInteger, Column, String, DateTime
from sqlalchemy.dialects.mysql import BIGINT

from config.database import Base


class OaContractAttachment(Base):
    """
    销售合同附件表
    """
    __tablename__ = 'oa_contract_attachment'
    __table_args__ = {'comment': '销售合同附件表'}

    id = Column(BIGINT(unsigned=True), primary_key=True, nullable=False, autoincrement=True, comment='主键ID')
    contract_id = Column(BIGINT(unsigned=True), nullable=False, comment='关联的销售合同ID')
    file_name = Column(String(255), nullable=False, comment='原始文件名')
    file_path = Column(String(500), nullable=False, comment='文件存储路径(相对路径)')
    file_size = Column(BIGINT(unsigned=True), nullable=False, default=0, comment='文件大小(字节)')
    file_ext = Column(String(20), nullable=True, comment='文件扩展名')
    file_mime = Column(String(100), nullable=True, comment='文件MIME类型')
    sort = Column(BIGINT(unsigned=True), nullable=False, default=0, comment='排序值')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')
    delete_time = Column(BigInteger, nullable=True, default=0, comment='软删除时间')
