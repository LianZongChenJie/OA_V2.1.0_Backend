from sqlalchemy import BigInteger, Column, Integer, String, Text

from config.database import Base


class OaOfficialDocs(Base):
    """
    公文表
    """

    __tablename__ = 'oa_official_docs'
    __table_args__ = {'comment': '公文表'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='公文 ID')
    title = Column(String(255), nullable=False, server_default="''", comment='公文主题')
    code = Column(String(100), nullable=False, server_default="''", comment='公文编号')
    secrets = Column(Integer, nullable=False, server_default='1', comment='密级程度:1 公开，2 秘密，3 机密')
    urgency = Column(Integer, nullable=False, server_default='1', comment='紧急程度:1 普通，2 紧急，3 加急')
    send_uids = Column(String(255), nullable=False, server_default="''", comment='主送 uid')
    copy_uids = Column(String(255), nullable=False, server_default="''", comment='抄送 uid')
    share_uids = Column(String(255), nullable=False, server_default="''", comment='分享查阅 uid')
    content = Column(Text, nullable=True, comment='公文内容')
    file_ids = Column(String(255), nullable=False, server_default="''", comment='附件 ids，如:1,2,3')
    draft_uid = Column(Integer, nullable=False, server_default='0', comment='拟稿人')
    did = Column(Integer, nullable=False, server_default='0', comment='拟稿部门')
    draft_time = Column(BigInteger, nullable=False, server_default='0', comment='拟稿日期')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='创建人')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')
    check_status = Column(Integer, nullable=False, server_default='0', comment='审核状态:0 待审核，1 审核中，2 审核通过，3 审核不通过，4 撤销审核')
    check_flow_id = Column(Integer, nullable=False, server_default='0', comment='审核流程 id')
    check_step_sort = Column(Integer, nullable=False, server_default='0', comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, server_default="''", comment='当前审批人 ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, server_default="''", comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, server_default="''", comment='历史审批人 ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, server_default="''", comment='抄送人 ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, server_default='0', comment='审核通过时间')
