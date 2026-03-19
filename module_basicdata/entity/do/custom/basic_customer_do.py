from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger
from config.database import Base
class OaBasicCustomer(Base):
    """客户常规数据实体类"""

    __tablename__ = 'oa_basic_customer'
    __table_args__ = {'comment': '客户常规数据'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    types = Column(String(100), nullable=False, default='', comment='数据类型:1客户状态,2客户意向,3跟进方式,4销售阶段，5看后期增加')
    title = Column(String(100), nullable=False, default='', comment='名称')

    # 状态
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1删除 0禁用 1启用')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}