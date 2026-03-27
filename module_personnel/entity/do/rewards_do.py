from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, BigInteger, SmallInteger,DECIMAL, Text
from typing import Optional
from config.database import Base
from decimal import Decimal
class OaRewards(Base):
    """员工奖罚表实体类（SQLAlchemy 2.0 风格）"""
    __tablename__ = 'oa_rewards'
    __table_args__ = {'comment': '员工奖罚表'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    uid: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='员工ID')
    types: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, comment='奖罚类型:1奖励2惩罚')
    rewards_cate: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='奖罚项目')
    rewards_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='奖罚日期')
    cost: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False, default=0.00, comment='金额')
    thing: Mapped[str] = mapped_column(String(255), nullable=False, default='', comment='物品')
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment='状态:1未执行2已执行')
    file_ids: Mapped[str] = mapped_column(String(500), nullable=False, default='', comment='附件')
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment='备注说明')
    admin_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='创建人')
    create_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='添加时间')
    update_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='修改时间')
    delete_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}