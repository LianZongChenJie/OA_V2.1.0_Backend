from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text
from config.database import Base
from sqlalchemy import Index


class OaNews(Base):
    """公司新闻表实体类"""

    __tablename__ = 'oa_news'
    __table_args__ = (
        Index('idx_create_time', 'create_time'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '公司新闻表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    title = Column(String(225), nullable=True, comment='标题')
    content = Column(Text, nullable=False, comment='新闻内容')
    src = Column(String(100), nullable=True, comment='关联链接')
    sort = Column(Integer, nullable=False, default=0, comment='排序')
    file_ids = Column(String(500), nullable=False, default='', comment='相关附件')
    admin_id = Column(Integer, nullable=False, default=0, comment='发布人id')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}