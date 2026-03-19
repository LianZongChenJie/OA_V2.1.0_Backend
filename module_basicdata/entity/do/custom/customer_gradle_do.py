from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger
from config.database import Base
class OaCustomerGrade(Base):
    """客户等级实体类"""

    __tablename__ = 'oa_customer_grade'
    __table_args__ = {'comment': '客户等级'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    title = Column(String(100), nullable=False, default='', comment='客户等级名称')

    # 排序
    sort = Column(Integer, nullable=False, default=0, comment='排序，越大越靠前')

    # 状态
    status = Column(SmallInteger, nullable=False, default=1, comment='状态: 0禁用 1启用')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}