"""add service customer settlement

Revision ID: 7f3a9c1d5e82
Revises:
Create Date: 2026-11-20 13:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f3a9c1d5e82'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'oa_service_customer_settlement',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('stat_year', sa.SmallInteger(), server_default='0', nullable=False, comment='年度，如 2026'),
        sa.Column('stat_month', sa.SmallInteger(), server_default='0', nullable=False, comment='月份，1-12'),
        sa.Column('customer_name', sa.String(length=255), server_default='', nullable=False, comment='客户名称'),
        sa.Column('employee_name', sa.String(length=255), server_default='', nullable=False, comment='姓名'),
        sa.Column('position_name', sa.String(length=100), server_default='', nullable=False, comment='职位'),
        sa.Column('level_name', sa.String(length=100), server_default='', nullable=False, comment='级别'),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False, comment='单价（元）'),
        sa.Column('actual_attendance_days', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False, comment='实际出勤（天）'),
        sa.Column('leave_days', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False, comment='请假（天）'),
        sa.Column('overtime_days', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False, comment='加班（天）'),
        sa.Column('comp_off_days', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False, comment='调休（天）'),
        sa.Column('payable_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False, comment='实际应结算费用（元）'),
        sa.Column('settled_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False, comment='实际结算费用（元）'),
        sa.Column('is_settled', sa.SmallInteger(), server_default='0', nullable=False, comment='是否结算：0否 1是'),
        sa.Column('remark', sa.String(length=1000), server_default='', nullable=False, comment='备注'),
        sa.Column('admin_id', sa.Integer(), server_default='0', nullable=False, comment='创建人'),
        sa.Column('create_time', sa.BigInteger(), server_default='0', nullable=False, comment='创建时间（秒）'),
        sa.Column('update_time', sa.BigInteger(), server_default='0', nullable=False, comment='更新时间（秒）'),
        sa.Column('delete_time', sa.BigInteger(), server_default='0', nullable=False, comment='删除时间（秒）'),
        sa.Column('tenant_id', sa.BigInteger(), server_default='1', nullable=False, comment='租户ID'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'stat_year', 'stat_month', 'customer_name', 'employee_name', 'delete_time',
            name='uk_year_month_customer_employee'
        ),
        mysql_comment='服务客户结算表',
    )
    op.create_index('idx_year_month', 'oa_service_customer_settlement', ['stat_year', 'stat_month'])
    op.create_index('idx_customer_name', 'oa_service_customer_settlement', ['customer_name'])
    op.create_index('idx_employee_name', 'oa_service_customer_settlement', ['employee_name'])
    op.create_index('idx_is_settled', 'oa_service_customer_settlement', ['is_settled'])
    op.create_index('idx_update_time', 'oa_service_customer_settlement', ['update_time'])
    op.create_index('idx_delete_time', 'oa_service_customer_settlement', ['delete_time'])


def downgrade() -> None:
    op.drop_index('idx_delete_time', table_name='oa_service_customer_settlement')
    op.drop_index('idx_update_time', table_name='oa_service_customer_settlement')
    op.drop_index('idx_is_settled', table_name='oa_service_customer_settlement')
    op.drop_index('idx_employee_name', table_name='oa_service_customer_settlement')
    op.drop_index('idx_customer_name', table_name='oa_service_customer_settlement')
    op.drop_index('idx_year_month', table_name='oa_service_customer_settlement')
    op.drop_table('oa_service_customer_settlement')
