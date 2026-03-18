from config.database import Base
from sqlalchemy import Column, Integer, String, SmallInteger
class OaArea(Base):
    """中国省市区数据实体类"""

    __tablename__ = 'oa_area'
    __table_args__ = {'comment': '中国省市区数据表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 层级关系
    pid = Column(Integer, nullable=False, default=0, comment='父级')

    # 名称信息
    name = Column(String(50), nullable=False, default='', comment='名称')
    shortname = Column(String(30), nullable=False, default='', comment='简称')

    # 地理位置
    longitude = Column(String(30), nullable=False, default='', comment='经度')
    latitude = Column(String(30), nullable=False, default='', comment='纬度')

    # 层级和排序
    level = Column(SmallInteger, nullable=False, default=0, comment='级别：1省/直辖市 2市 3区/县')
    sort = Column(Integer, nullable=False, default=0, comment='排序')

    # 状态
    status = Column(SmallInteger, nullable=False, default=1, comment='状态:默认1有效')


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    