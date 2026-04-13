from sqlalchemy import Column, Integer, String, BigInteger, Text, DECIMAL
from config.database import Base


class OaOvertimes(Base):
    """
    加班表
    """
    __tablename__ = 'oa_overtimes'
    __table_args__ = {'comment': '加班表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    start_date = Column(BigInteger, nullable=False, server_default='0', comment='开始日期')
    end_date = Column(BigInteger, nullable=False, server_default='0', comment='结束日期')
    start_span = Column(Integer, nullable=False, server_default='0', comment='时间段:1上午,2下午')
    end_span = Column(Integer, nullable=False, server_default='0', comment='时间段:1上午,2下午')
    duration = Column(DECIMAL(precision=10, scale=1), nullable=False, server_default='0.0', comment='时长(工作日)')
    reason = Column(Text, nullable=False, comment='出差原因')
    file_ids = Column(String(500), nullable=False, server_default='', comment='附件，如:1,2,3')
    check_status = Column(Integer, nullable=False, server_default='0', comment='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id = Column(Integer, nullable=False, server_default='0', comment='审核流程id')
    check_step_sort = Column(Integer, nullable=False, server_default='0', comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, server_default='', comment='当前审批人ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, server_default='', comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, server_default='', comment='历史审批人ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, server_default='', comment='抄送人ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, server_default='0', comment='审核通过时间')
    admin_id = Column(Integer, nullable=False, comment='创建人ID')
    did = Column(Integer, nullable=False, comment='创建人部门ID')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')