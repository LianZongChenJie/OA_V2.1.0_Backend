from datetime import datetime

from sqlalchemy import BigInteger, Column, Integer, String, Text, DECIMAL

from config.database import Base


class OaPurchase(Base):
    """
    采购合同表
    """

    __tablename__ = 'oa_purchase'
    __table_args__ = {'comment': '采购合同表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    pid = Column(Integer, nullable=False, default=0, comment='父协议 id')
    code = Column(String(255), nullable=False, default='', comment='合同编号')
    name = Column(String(255), nullable=False, default='', comment='合同名称')
    cate_id = Column(Integer, nullable=False, default=0, comment='分类 id')
    types = Column(Integer, nullable=False, default=1, comment='合同性质:1 普通采购 2 物品采购 3 服务采购')
    subject_id = Column(String(255), nullable=False, default='', comment='签约主体')
    supplier_id = Column(Integer, nullable=False, default=0, comment='关联供应商 ID')
    supplier = Column(String(255), nullable=False, default='', comment='供应商名称')
    contact_name = Column(String(255), nullable=False, default='', comment='供应商代表')
    contact_mobile = Column(String(255), nullable=False, default='', comment='供应商电话')
    contact_address = Column(String(255), nullable=False, default='', comment='供应商地址')
    start_time = Column(BigInteger, nullable=False, default=0, comment='合同开始时间')
    end_time = Column(BigInteger, nullable=False, default=0, comment='合同结束时间')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    prepared_uid = Column(Integer, nullable=False, default=0, comment='合同制定人')
    sign_uid = Column(Integer, nullable=False, default=0, comment='合同签订人')
    keeper_uid = Column(Integer, nullable=False, default=0, comment='合同保管人')
    share_ids = Column(String(500), nullable=False, default='', comment='共享人员，如:1,2,3')
    file_ids = Column(String(500), nullable=False, default='', comment='相关附件，如:1,2,3')
    seal_ids = Column(String(500), nullable=False, default='', comment='盖章合同附件，如:1,2,3')
    sign_time = Column(BigInteger, nullable=False, default=0, comment='合同签订时间')
    did = Column(Integer, nullable=False, default=0, comment='合同所属部门')
    cost = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='合同金额')
    content = Column(Text, nullable=True, comment='合同内容')
    stop_uid = Column(Integer, nullable=False, default=0, comment='中止人')
    stop_time = Column(BigInteger, nullable=False, default=0, comment='中止时间')
    stop_remark = Column(Text, nullable=True, comment='中止备注信息')
    void_uid = Column(Integer, nullable=False, default=0, comment='作废人')
    void_time = Column(BigInteger, nullable=False, default=0, comment='作废时间')
    void_remark = Column(Text, nullable=True, comment='作废备注信息')
    archive_uid = Column(Integer, nullable=False, default=0, comment='归档人')
    archive_time = Column(BigInteger, nullable=False, default=0, comment='归档时间')
    remark = Column(Text, nullable=True, comment='备注信息')
    create_time = Column(BigInteger, nullable=False, default=0, comment='添加时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='修改时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    check_status = Column(Integer, nullable=False, default=0, comment='审核状态:0 待审核，1 审核中，2 审核通过，3 审核不通过，4 撤销审核')
    check_flow_id = Column(Integer, nullable=False, default=0, comment='审核流程 id')
    check_step_sort = Column(Integer, nullable=False, default=0, comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, default='', comment='当前审批人 ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, default='', comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, default='', comment='历史审批人 ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, default='', comment='抄送人 ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, default=0, comment='审核通过时间')

