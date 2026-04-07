from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Index, Text
from config.database import Base
from sqlalchemy.dialects.mysql import DECIMAL


class OaInvoice(Base):
    """发票表实体类"""

    __tablename__ = 'oa_invoice'
    __table_args__ = (
        Index('idx_code', 'code'),
        Index('idx_customer_id', 'customer_id'),
        Index('idx_contract_id', 'contract_id'),
        Index('idx_project_id', 'project_id'),
        Index('idx_admin_id', 'admin_id'),
        Index('idx_check_status', 'check_status'),
        Index('idx_open_status', 'open_status'),
        Index('idx_enter_status', 'enter_status'),
        Index('idx_create_time', 'create_time'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '发票表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    code = Column(String(100), nullable=False, default='', comment='发票号码')
    customer_id = Column(Integer, nullable=False, default=0, comment='关联客户ID')
    contract_id = Column(Integer, nullable=False, default=0, comment='关联合同协议ID')
    project_id = Column(Integer, nullable=False, default=0, comment='关联项目ID')
    amount = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='发票金额')
    did = Column(Integer, nullable=False, default=0, comment='发票申请部门')
    admin_id = Column(Integer, nullable=False, default=0, comment='发票申请人')
    open_status = Column(SmallInteger, nullable=True, default=0, comment='开票状态：0未开票 1已开票 2已作废')
    open_admin_id = Column(Integer, nullable=False, default=0, comment='发票开具人')
    open_time = Column(BigInteger, nullable=False, default=0, comment='发票开具时间')
    delivery = Column(String(100), nullable=False, default='', comment='快递单号')
    types = Column(SmallInteger, nullable=True, default=0, comment='抬头类型：1企业2个人')
    invoice_type = Column(SmallInteger, nullable=True, default=0,
                          comment='发票类型：1增值税专用发票,2普通发票,3专用发票')
    invoice_subject = Column(Integer, nullable=False, default=0, comment='关联发票主体ID')
    invoice_title = Column(String(100), nullable=False, default='', comment='开票抬头')
    invoice_tax = Column(String(100), nullable=False, default='', comment='纳税人识别号')
    invoice_phone = Column(String(100), nullable=False, default='', comment='电话号码')
    invoice_address = Column(String(100), nullable=False, default='', comment='地址')
    invoice_bank = Column(String(100), nullable=False, default='', comment='开户银行')
    invoice_account = Column(String(100), nullable=False, default='', comment='银行账号')
    invoice_banking = Column(String(100), nullable=False, default='', comment='银行营业网点')
    file_ids = Column(String(500), nullable=False, default='', comment='附件ID，如:1,2,3')
    other_file_ids = Column(String(500), nullable=False, default='', comment='其他附件ID，如:1,2,3')
    remark = Column(Text, nullable=True, comment='备注')
    enter_amount = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='已到账金额')
    enter_status = Column(SmallInteger, nullable=True, default=0, comment='回款状态：0未回款 1部分回款 2全部回款')
    enter_time = Column(BigInteger, nullable=False, default=0, comment='最新回款时间')
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


class OaInvoiceIncome(Base):
    """发票到账记录表实体类"""

    __tablename__ = 'oa_invoice_income'
    __table_args__ = (
        Index('idx_invoice_id', 'invoice_id'),
        Index('idx_admin_id', 'admin_id'),
        Index('idx_enter_time', 'enter_time'),
        Index('idx_create_time', 'create_time'),
        Index('idx_status', 'status'),
        {'comment': '发票到账记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    invoice_id = Column(Integer, nullable=False, default=0, comment='发票ID')
    amount = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='到账金额')
    admin_id = Column(Integer, nullable=False, default=0, comment='到账登记人')
    enter_time = Column(BigInteger, nullable=False, default=0, comment='到账时间')
    remarks = Column(Text, nullable=True, comment='备注')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1删除 0禁用 1正常 6作废')