from sqlalchemy import Column, Integer, Text, BigInteger, SmallInteger, Index
from config.database import Base
from sqlalchemy.dialects.mysql import DECIMAL

class OaExpenseInterfix(Base):
    """报销关联数据表实体类"""

    __tablename__ = 'oa_expense_interfix'
    __table_args__ = (
        Index('idx_exid', 'exid'),
        Index('idx_admin_id', 'admin_id'),
        Index('idx_cate_id', 'cate_id'),
        Index('idx_create_time', 'create_time'),
        {'comment': '报销关联数据表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    exid = Column(Integer, nullable=False, default=0, comment='报销ID')
    amount = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='金额')
    cate_id = Column(SmallInteger, nullable=True, default=1, comment='报销类型ID')
    remarks = Column(Text, nullable=True, comment='备注')
    admin_id = Column(Integer, nullable=False, default=0, comment='登记人')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
