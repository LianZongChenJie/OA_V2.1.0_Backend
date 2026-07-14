"""
投标文件知识库模块 DO 实体类
"""
from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger


class OaBidDocument(Base):
    """投标文件信息表实体类"""

    __tablename__ = 'oa_bid_document'
    __table_args__ = {'comment': '投标文件信息表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    bid_uuid = Column(String(64), nullable=False, unique=True, comment='投标文件UUID')
    file_name = Column(String(256), nullable=False, default='', comment='原始文件名')
    bid_name = Column(String(256), nullable=False, default='', comment='投标项目名称')
    bid_code = Column(String(128), nullable=False, default='', comment='项目编号')
    company_name = Column(String(256), nullable=False, default='', comment='投标公司')
    total_pages = Column(Integer, nullable=False, default=0, comment='总页数')
    resume_count = Column(Integer, nullable=False, default=0, comment='包含简历数量')
    status = Column(SmallInteger, nullable=False, default=1, comment='状态:0删除,1正常')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def __repr__(self) -> str:
        return f"<OaBidDocument(id={self.id}, bid_name='{self.bid_name}', bid_code='{self.bid_code}')>"
