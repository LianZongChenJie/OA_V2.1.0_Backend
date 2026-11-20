"""alter hr cost entry_record_date to enum string

Revision ID: 3c8e1f2a5b74
Revises: 9b2e7c4f1a63
Create Date: 2026-11-20 16:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = '3c8e1f2a5b74'
down_revision = '9b2e7c4f1a63'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 旧值均为时间戳数字，转字符串后不属于枚举，先清空避免脏数据
    op.execute(
        "UPDATE oa_hr_cost SET entry_record_date = '' "
        "WHERE entry_record_date NOT IN ('新入职', '重新入职')"
    )
    op.alter_column(
        'oa_hr_cost',
        'entry_record_date',
        existing_type=sa.BigInteger(),
        type_=sa.String(length=20),
        server_default='',
        existing_nullable=False,
        comment='入职记录（新入职/重新入职）',
    )


def downgrade() -> None:
    op.alter_column(
        'oa_hr_cost',
        'entry_record_date',
        existing_type=sa.String(length=20),
        type_=sa.BigInteger(),
        server_default='0',
        existing_nullable=False,
        comment='入职记录（秒）',
    )
