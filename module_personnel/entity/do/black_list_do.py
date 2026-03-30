from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, BigInteger, SmallInteger, Text
from config.database import Base
from typing import Optional

class OaBlacklist(Base):
    """黑名单表实体类（SQLAlchemy 2.0 风格）"""
    __tablename__ = 'oa_blacklist'
    __table_args__ = {'comment': '黑名单表'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name: Mapped[str] = mapped_column(String(255), nullable=False, default='', comment='姓名')
    mobile: Mapped[str] = mapped_column(String(255), nullable=False, default='', comment='手机号码')
    idcard: Mapped[str] = mapped_column(String(255), nullable=False, default='', comment='身份证')
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment='备注信息')
    admin_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='创建人')
    create_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='申请时间')
    update_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='更新信息时间')
    delete_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
