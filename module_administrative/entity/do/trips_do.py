from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text, DECIMAL
from config.database import Base
from sqlalchemy import Index


class OaTrips(Base):
    """
    出差申请表
    """

    __tablename__ = 'oa_trips'
    __table_args__ = (
        Index('idx_admin_id', 'admin_id'),
        Index('idx_create_time', 'create_time'),
        Index('idx_start_date', 'start_date'),
        Index('idx_delete_time', 'delete_time'),
        {'comment': '出差表'}
    )

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='出差 ID')
    start_date = Column(BigInteger, nullable=False, server_default='0', comment='开始日期')
    end_date = Column(BigInteger, nullable=False, server_default='0', comment='结束日期')
    start_span = Column(Integer, nullable=False, server_default='0', comment='时间段:1上午,2下午')
    end_span = Column(Integer, nullable=False, server_default='0', comment='时间段:1上午,2下午')
    duration = Column(DECIMAL(10, 1), nullable=False, server_default='0.0', comment='时长(工作日)')
    reason = Column(Text, nullable=False, comment='出差原因')
    file_ids = Column(String(500), nullable=False, server_default="''", comment='附件 ids，如:1,2,3')
    check_status = Column(SmallInteger, nullable=False, server_default='0', comment='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id = Column(Integer, nullable=False, server_default='0', comment='审核流程 id')
    check_step_sort = Column(Integer, nullable=False, server_default='0', comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, server_default="''", comment='当前审批人 ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, server_default="''", comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, server_default="''", comment='历史审批人 ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, server_default="''", comment='抄送人 ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, server_default='0', comment='审核通过时间')
    admin_id = Column(Integer, nullable=False, comment='创建人ID')
    did = Column(Integer, nullable=False, comment='创建人部门ID')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')