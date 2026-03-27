from config.database import Base
from sqlalchemy import Column, Integer, String, SmallInteger, Text, BigInteger,DECIMAL
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from decimal import Decimal

class OaLaborContract(Base):
    """员工合同表实体类（SQLAlchemy 2.0 风格）"""
    __tablename__ = 'oa_labor_contract'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    renewal_pid: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='续签母合同')
    change_pid: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='变更母合同')
    uid: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='员工ID')
    cate: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1,
                                      comment='合同类别:1劳动合同,2劳务合同,3保密协议')
    types: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1,
                                       comment='合同类型:1新签合同,2续签合同,3变更合同')
    enterprise_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='关联企业主体ID')
    properties: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1,
                                            comment='合同属性:1初级职称,2中级职称,3高级职称')
    code: Mapped[str] = mapped_column(String(255), nullable=False, default='', comment='合同编号')
    title: Mapped[str] = mapped_column(String(255), nullable=False, default='', comment='合同名称')
    sign_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='签订时间')
    start_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='生效时间')
    end_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='失效时间')
    secure_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='解除时间')
    trial_months: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='试用月数')
    trial_end_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='试用结束时间')
    trial_salary: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False, default=0.00, comment='试用工资')
    worker_salary: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False, default=0.00, comment='转正工资')
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1,
                                        comment='合同状态:1正常,2已到期,3已解除')
    file_ids: Mapped[str] = mapped_column(String(500), nullable=False, default='', comment='附件')
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment='备注说明')
    admin_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='创建人ID')
    create_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='添加时间')
    update_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='修改时间')
    delete_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='删除时间')
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}