from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Index
from config.database import Base
from sqlalchemy.dialects.mysql import DECIMAL


class OaLoan(Base):
    """借支表实体类"""

    __tablename__ = 'oa_loan'
    __table_args__ = (
        Index('idx_admin_id', 'admin_id'),
        Index('idx_did', 'did'),
        Index('idx_check_status', 'check_status'),
        Index('idx_pay_status', 'pay_status'),
        Index('idx_back_status', 'back_status'),
        Index('idx_balance_status', 'balance_status'),
        Index('idx_create_time', 'create_time'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '借支表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    subject_id = Column(Integer, nullable=False, default=0, comment='借支企业主体')
    code = Column(String(100), nullable=False, default='', comment='借支编码')
    title = Column(String(500), nullable=False, default='', comment='借款主题')
    cost = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='借支金额')
    types = Column(SmallInteger, nullable=False, default=1, comment='借支类型：1日常备用金,2项目预支款')
    loan_time = Column(BigInteger, nullable=False, default=0, comment='预期借支日期')
    plan_time = Column(BigInteger, nullable=False, default=0, comment='预计还款日期')
    content = Column(String(1000), default='', comment='借支理由')
    admin_id = Column(Integer, nullable=False, default=0, comment='借支人')
    did = Column(Integer, nullable=False, default=0, comment='借支部门ID')
    balance_cost = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='已冲账金额')
    balance_status = Column(SmallInteger, nullable=False, default=0, comment='冲账状态 0待冲账,1部分冲账,2已冲账')
    project_id = Column(Integer, nullable=False, default=0, comment='关联项目ID')
    file_ids = Column(String(500), nullable=False, default='', comment='附件ID，如:1,2,3')
    pay_status = Column(SmallInteger, nullable=False, default=0, comment='打款状态 0待打款,1已打款')
    pay_admin_id = Column(Integer, nullable=False, default=0, comment='打款人ID')
    pay_time = Column(BigInteger, nullable=False, default=0, comment='最后打款时间')
    back_status = Column(SmallInteger, nullable=False, default=0, comment='还款状态 0待还款,1已还款')
    back_admin_id = Column(Integer, nullable=False, default=0, comment='还款操作人ID')
    back_time = Column(BigInteger, nullable=False, default=0, comment='最后还款时间')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    check_status = Column(SmallInteger, nullable=False, default=0,
                          comment='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id = Column(Integer, nullable=False, default=0, comment='审核流程id')
    check_step_sort = Column(Integer, nullable=False, default=0, comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, default='', comment='当前审批人ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, default='', comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, default='', comment='历史审批人ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, default='', comment='抄送人ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, default=0, comment='审核通过时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
