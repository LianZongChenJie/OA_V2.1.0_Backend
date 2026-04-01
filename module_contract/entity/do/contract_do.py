# module_contract/entity/do/contract_do.py
from sqlalchemy import BigInteger, Column, Integer, String, Text, Float, SmallInteger
from sqlalchemy.dialects.mysql import MEDIUMTEXT

from config.database import Base


class OaContract(Base):
    """
    销售合同表 ORM 模型
    """
    __tablename__ = 'oa_contract'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='合同 ID')
    pid = Column(Integer, nullable=False, default=0, comment='父协议 id')
    code = Column(String(255), nullable=False, default='', comment='合同编号')
    name = Column(String(255), nullable=False, default='', comment='合同名称')
    cate_id = Column(Integer, nullable=False, default=0, comment='分类 id')
    types = Column(SmallInteger, nullable=False, default=1, comment='合同性质:1 普通合同 2 商品合同 3 服务合同')
    subject_id = Column(String(255), nullable=False, default='', comment='签约主体')
    customer_id = Column(Integer, nullable=False, default=0, comment='关联客户 ID，预设数据')
    chance_id = Column(Integer, nullable=False, default=0, comment='销售机会 id')
    customer = Column(String(255), nullable=False, default='', comment='客户名称')
    contact_name = Column(String(255), nullable=False, default='', comment='客户代表')
    contact_mobile = Column(String(255), nullable=False, default='', comment='客户电话')
    contact_address = Column(String(255), nullable=False, default='', comment='客户地址')
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
    cost = Column(Float(15, 2), nullable=False, default=0.00, comment='合同金额')
    content = Column(MEDIUMTEXT, comment='合同内容')
    is_tax = Column(SmallInteger, nullable=False, default=0, comment='是否含税：0 未含税，1 含税')
    tax = Column(Float(15, 2), nullable=False, default=0.00, comment='税点')
    stop_uid = Column(Integer, nullable=False, default=0, comment='中止人')
    stop_time = Column(BigInteger, nullable=False, default=0, comment='中止时间')
    stop_remark = Column(MEDIUMTEXT, comment='中止备注信息')
    void_uid = Column(Integer, nullable=False, default=0, comment='作废人')
    void_time = Column(BigInteger, nullable=False, default=0, comment='作废时间')
    void_remark = Column(MEDIUMTEXT, comment='作废备注信息')
    archive_uid = Column(Integer, nullable=False, default=0, comment='归档人')
    archive_time = Column(BigInteger, nullable=False, default=0, comment='归档时间')
    remark = Column(MEDIUMTEXT, comment='备注信息')
    create_time = Column(BigInteger, nullable=False, default=0, comment='添加时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='修改时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    check_status = Column(SmallInteger, nullable=False, default=0, comment='审核状态:0 待审核，1 审核中，2 审核通过，3 审核不通过，4 撤销审核')
    check_flow_id = Column(Integer, nullable=False, default=0, comment='审核流程 id')
    check_step_sort = Column(Integer, nullable=False, default=0, comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, default='', comment='当前审批人 ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, default='', comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, default='', comment='历史审批人 ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, default='', comment='抄送人 ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, default=0, comment='审核通过时间')

