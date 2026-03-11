from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, DECIMAL, Date
from sqlalchemy.dialects.mysql import BIGINT

from config.database import Base
import enum

# 保留枚举类（供VO层校验用），但DO层不再使用Enum类型
class IsTenderSubmittedEnum(str, enum.Enum):
    """是否投标枚举"""
    YES = '是'
    NO = '否'

class HasTenderInvoiceEnum(str, enum.Enum):
    """标书款发票枚举"""
    YES = '是'
    NO = '否'

class IsDepositPaidEnum(str, enum.Enum):
    """是否缴纳保证金枚举"""
    YES = '是'
    NO = '否'

class IsDepositRefundedEnum(str, enum.Enum):
    """是否退回保证金枚举"""
    YES = '是'
    NO = '否'

class BidResultEnum(str, enum.Enum):
    """中标结果枚举"""
    WIN = '中标'
    LOSE = '未中标'
    PENDING = '待公布'

class OaProjectTender(Base):
    """项目投标信息表"""
    __tablename__ = 'oa_project_tender'
    __table_args__ = {'comment': '项目投标信息表'}

    id = Column(BIGINT(unsigned=True), primary_key=True, nullable=False, autoincrement=True, comment='主键 ID')
    month = Column(String(10), nullable=True, comment='月份')
    tender_leader = Column(String(50), nullable=True, comment='标书负责人')
    purchase_date = Column(Date, nullable=True, comment='购买日期')
    customer_name = Column(String(100), nullable=True, comment='客户名称')
    project_name = Column(String(200), nullable=True, comment='项目名称')
    tender_agency = Column(String(100), nullable=True, comment='招标机构')
    project_cycle = Column(String(50), nullable=True, comment='项目周期')
    shortlisted_countries = Column(String(20), nullable=True, comment='入围家数')
    budget_amount = Column(DECIMAL(precision=18, scale=2), nullable=True, comment='预算金额（元）')
    bid_opening_date = Column(Date, nullable=True, comment='开标日期')
    is_tender_submitted = Column(String(2), nullable=True, comment='是否投标')
    non_tender_reason = Column(String(200), nullable=True, comment='未投原因')
    tender_document_fee = Column(DECIMAL(precision=10, scale=2), nullable=True, comment='标书款（元）')
    has_tender_invoice = Column(String(2), nullable=True, comment='标书款发票')
    is_deposit_paid = Column(String(2), nullable=True, comment='是否缴纳保证金')
    tender_deposit = Column(DECIMAL(precision=18, scale=2), nullable=True, comment='投标保证金（元）')
    deposit_account_name = Column(String(100), nullable=True, comment='保证金账户名')
    deposit_bank = Column(String(100), nullable=True, comment='保证金开户行')
    deposit_account_no = Column(String(50), nullable=True, comment='保证金账号')
    is_deposit_refunded = Column(String(2), nullable=True, comment='是否退回保证')
    bid_result = Column(String(20), nullable=True, comment='中标结果')
    bid_service_fee = Column(DECIMAL(precision=10, scale=2), nullable=True, comment='中标服务费')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    delete_time = Column(BigInteger, nullable=True, default=0, comment='删除时间')
    sort = Column(BigInteger, nullable=True, comment='排序值')

class OaProjectTenderAttachment(Base):
    """项目投标附件表"""
    __tablename__ = 'oa_project_tender_attachment'
    __table_args__ = {'comment': '项目投标附件表'}

    id = Column(BIGINT(unsigned=True), primary_key=True, nullable=False, autoincrement=True, comment='主键 ID')
    project_tender_id = Column(BIGINT(unsigned=True), nullable=False, comment='关联的项目投标记录 ID')
    file_name = Column(String(255), nullable=False, comment='原始文件名')
    file_path = Column(String(500), nullable=False, comment='文件存储路径（相对路径）')
    file_size = Column(BIGINT(unsigned=True), nullable=False, default=0, comment='文件大小（字节）')
    file_ext = Column(String(20), nullable=True, comment='文件扩展名')
    file_mime = Column(String(100), nullable=True, comment='文件 MIME 类型')
    sort = Column(BIGINT(unsigned=True), nullable=False, default=0, comment='排序值')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, onupdate=datetime.now, comment='更新时间')
    delete_time = Column(BigInteger, nullable=True, default=0, comment='软删除时间')