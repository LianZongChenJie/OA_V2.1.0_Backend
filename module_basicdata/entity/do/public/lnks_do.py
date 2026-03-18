from sqlalchemy import Column, Integer, String, SmallInteger
from config.database import Base

class OaLinks(Base):
    """办公工具实体类"""

    __tablename__ = 'oa_links'
    __table_args__ = {'comment': '办公工具'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    title = Column(String(255), nullable=False, default='', comment='小工具名称')
    logo = Column(Integer, nullable=False, default=0, comment='logo')
    url = Column(String(255), nullable=True, default='', comment='链接')

    # 配置信息
    target = Column(SmallInteger, nullable=False, default=1, comment='是否新窗口打开，1是,0否')
    sort = Column(Integer, nullable=False, default=0, comment='排序')

    # 时间戳
    create_time = Column(Integer, nullable=False, default=0, comment='创建时间')
    update_time = Column(Integer, nullable=False, default=0, comment='更新时间')
    delete_time = Column(Integer, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}