"""add hr cost

Revision ID: 9b2e7c4f1a63
Revises: 7f3a9c1d5e82
Create Date: 2026-11-20 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = '9b2e7c4f1a63'
down_revision = '7f3a9c1d5e82'
branch_labels = None
depends_on = None


MONEY = sa.Numeric(18, 6)


def upgrade() -> None:
    op.create_table(
        'oa_hr_cost',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('stat_month', sa.CHAR(length=7), server_default='', nullable=False, comment='月份 YYYY-MM'),
        sa.Column('employee_status', sa.String(length=20), server_default='', nullable=False, comment='员工状态'),
        sa.Column('city_id', sa.Integer(), server_default='0', nullable=False, comment='城市ID'),
        sa.Column('city_name', sa.String(length=100), server_default='', nullable=False, comment='城市名称快照'),
        sa.Column('org_id', sa.Integer(), server_default='0', nullable=False, comment='组织架构ID'),
        sa.Column('org_name', sa.String(length=100), server_default='', nullable=False, comment='组织架构名称快照'),
        sa.Column('employee_name', sa.String(length=100), server_default='', nullable=False, comment='姓名'),
        sa.Column('id_card', sa.String(length=32), nullable=False, comment='身份证号码'),
        sa.Column('entry_date', sa.BigInteger(), server_default='0', nullable=False, comment='入职日期'),
        sa.Column('entry_record_date', sa.String(length=20), server_default='', nullable=False, comment='入职记录'),
        sa.Column('project_name', sa.String(length=255), server_default='', nullable=False, comment='目前所在项目'),
        *[sa.Column(name, MONEY, server_default='0', nullable=False, comment=name) for name in [
            'contract_salary', 'base_salary', 'performance_salary', 'post_salary',
            'customer_fee_tax_included', 'computer_subsidy', 'meal_subsidy', 'bonus', 'subsidy',
            'deduction', 'other_deduction', 'gross_salary', 'pension_personal', 'medical_personal',
            'unemployment_personal', 'social_personal_total', 'housing_fund_personal',
            'taxable_salary', 'income_tax', 'bank_pay_amount', 'pension_company',
            'unemployment_company', 'injury_company', 'medical_maternity_company',
            'social_company_total', 'housing_fund_company', 'social_total', 'housing_fund_total',
            'company_total_cost', 'social_base', 'housing_fund_base',
            'tax_excluded_revenue', 'gross_profit', 'tax_declaration_amount',
        ]],
        sa.Column('salary_ratio', sa.Numeric(5, 2), server_default='1.00', nullable=False, comment='算薪比例'),
        sa.Column('attendance_days', sa.Numeric(10, 2), server_default='0', nullable=False, comment='考勤（天）'),
        sa.Column('remark', sa.String(length=1000), server_default='', nullable=False, comment='备注'),
        sa.Column('admin_id', sa.Integer(), server_default='0', nullable=False, comment='创建人'),
        sa.Column('create_time', sa.BigInteger(), server_default='0', nullable=False, comment='创建时间'),
        sa.Column('update_time', sa.BigInteger(), server_default='0', nullable=False, comment='更新时间'),
        sa.Column('delete_time', sa.BigInteger(), server_default='0', nullable=False, comment='删除时间'),
        sa.Column('tenant_id', sa.BigInteger(), server_default='1', nullable=False, comment='租户ID'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stat_month', 'id_card', 'delete_time', name='uk_month_id_card'),
        mysql_comment='人力总成本明细表',
    )
    for name, columns in [
        ('idx_stat_month', ['stat_month']),
        ('idx_org_id', ['org_id']),
        ('idx_city_id', ['city_id']),
        ('idx_employee_name', ['employee_name']),
        ('idx_delete_time', ['delete_time']),
    ]:
        op.create_index(name, 'oa_hr_cost', columns)


def downgrade() -> None:
    for name in ['idx_delete_time', 'idx_employee_name', 'idx_city_id', 'idx_org_id', 'idx_stat_month']:
        op.drop_index(name, table_name='oa_hr_cost')
    op.drop_table('oa_hr_cost')
