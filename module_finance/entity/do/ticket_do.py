from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Index, Text
from config.database import Base
from sqlalchemy.dialects.mysql import DECIMAL
class OaTicket(Base):
    """收票表实体类"""

    __tablename__ = 'oa_ticket'
    __table_args__ = (
        Index('idx_code', 'code'),
        Index('idx_supplier_id', 'supplier_id'),
        Index('idx_purchase_id', 'purchase_id'),
        Index('idx_customer_id', 'customer_id'),
        Index('idx_project_id', 'project_id'),
        Index('idx_admin_id', 'admin_id'),
        Index('idx_check_status', 'check_status'),
        Index('idx_pay_status', 'pay_status'),
        Index('idx_open_status', 'open_status'),
        Index('idx_create_time', 'create_time'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '收票表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    code = Column(String(100), nullable=False, default='', comment='发票号码')
    supplier_id = Column(Integer, nullable=False, default=0, comment='关联供应商ID')
    purchase_id = Column(Integer, nullable=False, default=0, comment='关联采购合同协议ID')
    customer_id = Column(Integer, nullable=False, default=0, comment='关联客户ID')
    project_id = Column(Integer, nullable=False, default=0, comment='关联项目ID')
    amount = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='发票金额')
    did = Column(Integer, nullable=False, default=0, comment='发票接受部门')
    admin_id = Column(Integer, nullable=False, default=0, comment='发票接受人')
    open_status = Column(SmallInteger, nullable=True, default=1, comment='开票状态：1正常 2已作废')
    open_time = Column(BigInteger, nullable=False, default=0, comment='发票开具时间')
    invoice_type = Column(SmallInteger, nullable=True, default=0, comment='发票类型：1增值税专用发票,2普通发票,3专用发票')
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
    pay_amount = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='已付款金额')
    cash_type = Column(Integer, nullable=True, default=1, comment='付款类型：1银行,2现金,3支付宝,4微信,5汇票,6支票,7托收,8其他')
    pay_status = Column(SmallInteger, nullable=True, default=0, comment='付款状态：0未付款 1部分付款 2全部付款')
    pay_time = Column(BigInteger, nullable=False, default=0, comment='最新回款时间')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    check_status = Column(SmallInteger, nullable=False, default=0, comment='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id = Column(Integer, nullable=False, default=0, comment='审核流程id')
    check_step_sort = Column(Integer, nullable=False, default=0, comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, default='', comment='当前审批人ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, default='', comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, default='', comment='历史审批人ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, default='', comment='抄送人ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, default=0, comment='审核通过时间')


class OaTicketPayment(Base):
    """收票付款记录表实体类"""

    __tablename__ = 'oa_ticket_payment'
    __table_args__ = (
        Index('idx_ticket_id', 'ticket_id'),
        Index('idx_admin_id', 'admin_id'),
        Index('idx_pay_time', 'pay_time'),
        Index('idx_create_time', 'create_time'),
        Index('idx_status', 'status'),
        {'comment': '收票付款记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    ticket_id = Column(Integer, nullable=False, default=0, comment='发票ID')
    amount = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='付款金额')
    admin_id = Column(Integer, nullable=False, default=0, comment='付款登记人')
    pay_time = Column(BigInteger, nullable=False, default=0, comment='付款时间')
    remarks = Column(Text, nullable=True, comment='备注')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1删除 0禁用 1正常 6作废')