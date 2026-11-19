from sqlalchemy import CHAR, DECIMAL, BigInteger, Column, Index, Integer, SmallInteger, String, UniqueConstraint

from config.database import Base


class OaProjectMonthly(Base):
    """项目月度台账 ORM 模型"""

    __tablename__ = 'oa_project_monthly'
    __table_args__ = (
        UniqueConstraint(
            'stat_month', 'project_name', 'customer_name', 'delete_time', name='uk_month_project_customer'
        ),
        Index('idx_stat_month', 'stat_month'),
        Index('idx_project_name', 'project_name'),
        Index('idx_customer_name', 'customer_name'),
        Index('idx_update_time', 'update_time'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '项目月度台账表'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    stat_month = Column(CHAR(7), nullable=False, server_default="''", comment='年度/统计月份 YYYY-MM')
    customer_name = Column(String(255), nullable=False, server_default="''", comment='客户名称')
    project_name = Column(String(255), nullable=False, server_default="''", comment='项目名称')
    contract_signed = Column(SmallInteger, nullable=False, server_default='0', comment='合同是否签订：0否 1是')
    planned_cost = Column(DECIMAL(15, 2), nullable=False, server_default='0.00', comment='预计投入成本')
    actual_cost = Column(DECIMAL(15, 2), nullable=False, server_default='0.00', comment='实际投入成本')
    planned_profit = Column(DECIMAL(15, 2), nullable=False, server_default='0.00', comment='预计项目利润')
    actual_profit = Column(DECIMAL(15, 2), nullable=False, server_default='0.00', comment='实际项目利润')
    collection_agreement = Column(String(500), nullable=False, server_default="''", comment='合同收款约定')
    invoiced_amount = Column(DECIMAL(15, 2), nullable=False, server_default='0.00', comment='实际开票金额')
    received_amount = Column(DECIMAL(15, 2), nullable=False, server_default='0.00', comment='实际收款金额')
    project_closed = Column(SmallInteger, nullable=False, server_default='0', comment='是否结项：0否 1是')
    project_id = Column(Integer, nullable=False, server_default='0', comment='关联旧项目ID（可选）')
    remark = Column(String(1000), nullable=False, server_default="''", comment='备注')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='创建人')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建/上传/新增时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')
    tenant_id = Column(BigInteger, nullable=False, server_default='1', comment='租户ID')
