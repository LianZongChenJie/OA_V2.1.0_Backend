from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.mysql import BIGINT

from config.database import Base

class OaWebsiteAccount(Base):
    """网站账号信息表"""
    __tablename__ = 'oa_website_account'
    __table_args__ = {'comment': '网站账号信息表'}

    id = Column(BIGINT(unsigned=True), primary_key=True, nullable=False, autoincrement=True, comment='主键 ID')
    website_name = Column(String(255), nullable=False, comment='网站名称')
    website_url = Column(String(1512), nullable=False, comment='网址')
    username = Column(String(100), nullable=True, comment='用户名')
    password = Column(String(100), nullable=True, comment='密码')
    has_uk = Column(String(200), nullable=True, comment='是否有 UK')
    remark = Column(Text, nullable=True, comment='说明')
    sort = Column(Integer, nullable=True, default=0, comment='排序字段，值越小越靠前')
    created_at = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    delete_time = Column(BigInteger, nullable=True, default=0, comment='删除时间')
    status = Column(String(100), nullable=True, comment='状态')
    create_time = Column(BigInteger, nullable=True, comment='创建时间戳')
    update_time = Column(BigInteger, nullable=True, comment='更新时间戳')
