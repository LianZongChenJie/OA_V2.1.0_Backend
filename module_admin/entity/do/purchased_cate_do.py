from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text


class OaPurchasedCate(Base):
    """采购品分类表实体类"""

    __tablename__ = 'oa_purchased_cate'
    __table_args__ = {'comment': '采购品分类'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    title = Column(String(100), nullable=False, default='', comment='分类名称')
    pid = Column(Integer, nullable=False, default=0, comment='分类 id（父级 ID）')
    sort = Column(Integer, nullable=False, default=0, comment='排序：越大越靠前')
    desc = Column(String(1000), nullable=False, default='', comment='分类说明')

    # 状态
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1 删除 0 禁用 1 启用')

    # 管理信息
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def __repr__(self) -> str:
        return f"<OaPurchasedCate(id={self.id}, title='{self.title}', pid={self.pid})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'pid': self.pid,
            'sort': self.sort,
            'desc': self.desc,
            'status': self.status,
            'admin_id': self.admin_id,
            'create_time': self.create_time,
            'update_time': self.update_time
        }
