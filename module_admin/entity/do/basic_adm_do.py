from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger


class OaBasicAdm(Base):
    """行政模块常规数据实体类"""

    __tablename__ = 'oa_basic_adm'
    __table_args__ = {'comment': '行政模块常规数据'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    types = Column(String(100), nullable=False, default='', comment='数据类型:1 车辆费用类型，2')
    title = Column(String(100), nullable=False, default='', comment='名称')

    # 状态
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1 删除 0 禁用 1 启用')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def __repr__(self) -> str:
        return f"<OaBasicAdm(id={self.id}, types='{self.types}', title='{self.title}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'types': self.types,
            'title': self.title,
            'status': self.status,
            'create_time': self.create_time,
            'update_time': self.update_time
        }

