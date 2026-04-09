"""
在线文档表实体类
"""
from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, Text


class OaArticle(Base):
    """在线文档表实体类"""

    __tablename__ = 'oa_article'
    __table_args__ = {'comment': '文档表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='文档ID')
    name = Column(String(255), nullable=False, default='', comment='文档标题')
    origin_url = Column(String(255), nullable=False, default='', comment='来源地址')
    file_ids = Column(String(500), nullable=False, default='', comment='相关附件')
    content = Column(Text, nullable=False, comment='文章内容')
    admin_id = Column(Integer, nullable=False, default=0, comment='作者')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def __repr__(self) -> str:
        return f"<OaArticle(id={self.id}, name='{self.name}')>"
