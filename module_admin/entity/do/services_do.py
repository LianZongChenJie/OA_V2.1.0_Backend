from config.database import Base
from sqlalchemy import Column, Integer, String, Numeric, Text, BigInteger, SmallInteger


class OaServices(Base):
    """服务表实体类"""

    __tablename__ = 'oa_services'
    __table_args__ = {'comment': '服务表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    title = Column(String(100), nullable=False, default='', comment='服务名称')
    cate_id = Column(Integer, nullable=False, default=0, comment='服务分类 id')
    price = Column(Numeric(15, 2), nullable=False, default=0.00, comment='服务费用')
    content = Column(Text, comment='服务描述')
    sort = Column(Integer, nullable=False, default=0, comment='排序')

    # 状态
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：0 禁用 1 启用')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def __repr__(self) -> str:
        return f"<OaServices(id={self.id}, title='{self.title}', cate_id={self.cate_id}, price={self.price})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'cate_id': self.cate_id,
            'price': float(self.price) if self.price else 0.00,
            'content': self.content,
            'sort': self.sort,
            'status': self.status,
            'create_time': self.create_time,
            'update_time': self.update_time,
            'delete_time': self.delete_time
        }
