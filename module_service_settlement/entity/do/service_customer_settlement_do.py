from sqlalchemy import BigInteger, DECIMAL, Column, Index, Integer, SmallInteger, String, UniqueConstraint

from config.database import Base


class OaServiceCustomerSettlement(Base):
    """服务客户结算 ORM 模型"""

    __tablename__ = 'oa_service_customer_settlement'
    __table_args__ = (
        UniqueConstraint(
            'stat_year', 'stat_month', 'customer_name', 'employee_name', 'delete_time',
            name='uk_year_month_customer_employee'
        ),
        Index('idx_year_month', 'stat_year', 'stat_month'),
        Index('idx_customer_name', 'customer_name'),
        Index('idx_employee_name', 'employee_name'),
        Index('idx_is_settled', 'is_settled'),
        Index('idx_update_time', 'update_time'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '服务客户结算表'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    stat_year = Column(SmallInteger, nullable=False, server_default='0', comment='年度，如 2026')
    stat_month = Column(SmallInteger, nullable=False, server_default='0', comment='月份，1-12')
    customer_name = Column(String(255), nullable=False, server_default="''", comment='客户名称')
    employee_name = Column(String(255), nullable=False, server_default="''", comment='姓名')
    position_name = Column(String(100), nullable=False, server_default="''", comment='职位')
    level_name = Column(String(100), nullable=False, server_default="''", comment='级别')
    unit_price = Column(DECIMAL(15, 2), nullable=False, server_default='0.00', comment='单价（元）')
    actual_attendance_days = Column(DECIMAL(10, 2), nullable=False, server_default='0.00', comment='实际出勤（天）')
    leave_days = Column(DECIMAL(10, 2), nullable=False, server_default='0.00', comment='请假（天）')
    overtime_days = Column(DECIMAL(10, 2), nullable=False, server_default='0.00', comment='加班（天）')
    comp_off_days = Column(DECIMAL(10, 2), nullable=False, server_default='0.00', comment='调休（天）')
    payable_amount = Column(DECIMAL(15, 2), nullable=False, server_default='0.00', comment='实际应结算费用（元）')
    settled_amount = Column(DECIMAL(15, 2), nullable=False, server_default='0.00', comment='实际结算费用（元）')
    is_settled = Column(SmallInteger, nullable=False, server_default='0', comment='是否结算：0否 1是')
    remark = Column(String(1000), nullable=False, server_default="''", comment='备注')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='创建人')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间（秒）')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间（秒）')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间（秒）')
    tenant_id = Column(BigInteger, nullable=False, server_default='1', comment='租户ID')
