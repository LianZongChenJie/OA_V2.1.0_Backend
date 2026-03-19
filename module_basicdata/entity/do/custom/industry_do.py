from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger
from config.database import Base
class OaIndustry(Base):
    """行业实体类"""

    __tablename__ = 'oa_industry'
    __table_args__ = {'comment': '行业'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    title = Column(String(100), nullable=False, default='', comment='行业名称')

    # 状态
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1删除 0禁用 1启用')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
