from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text
from config.database import Base


class OaMeetingRoom(Base):
    """
    会议室表
    """
    __tablename__ = 'oa_meeting_room'
    __table_args__ = {'comment': '会议室'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    title = Column(String(100), nullable=False, server_default="''", comment='会议室名称')
    keep_uid = Column(Integer, nullable=False, server_default='0', comment='会议室管理员 ID')
    address = Column(String(100), nullable=False, server_default="''", comment='地址楼层')
    device = Column(String(255), nullable=False, server_default="''", comment='会议室设备')
    num = Column(Integer, nullable=False, server_default='10', comment='可容纳人数')
    remark = Column(String(1000), nullable=True, comment='会议室描述')
    status = Column(SmallInteger, nullable=False, server_default='1', comment='状态：-1 删除 0 禁用 1 启用')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')


class OaMeetingOrder(Base):
    """
    会议室预定订单表
    """
    __tablename__ = 'oa_meeting_order'
    __table_args__ = {'comment': '会议室预定订单'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    room_id = Column(Integer, nullable=False, server_default='0', comment='会议室 ID')
    title = Column(String(225), nullable=True, comment='预定主题')
    start_date = Column(Integer, nullable=False, server_default='0', comment='开始时间')
    end_date = Column(Integer, nullable=False, server_default='0', comment='结束时间')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='发布人 id')
    did = Column(Integer, nullable=False, server_default='0', comment='主办部门')
    requirements = Column(String(500), nullable=False, server_default="''", comment='会议需求')
    num = Column(Integer, nullable=False, server_default='0', comment='人数')
    remark = Column(String(225), nullable=True, comment='备注信息')
    file_ids = Column(String(500), nullable=False, server_default="''", comment='相关附件')
    join_uids = Column(String(500), nullable=False, server_default="''", comment='与会人员')
    anchor_id = Column(Integer, nullable=False, server_default='0', comment='主持人 id')
    check_status = Column(Integer, nullable=False, server_default='0', comment='审核状态:0 待审核，1 审核中，2 审核通过，3 审核不通过，4 撤销审核')
    check_flow_id = Column(Integer, nullable=False, server_default='0', comment='审核流程 id')
    check_step_sort = Column(Integer, nullable=False, server_default='0', comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, server_default="''", comment='当前审批人 ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, server_default="''", comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, server_default="''", comment='历史审批人 ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, server_default="''", comment='抄送人 ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, server_default='0', comment='审核通过时间')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='申请时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新信息时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')


class OaMeetingRecords(Base):
    """
    会议纪要表
    """
    __tablename__ = 'oa_meeting_records'
    __table_args__ = {'comment': '会议纪要'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    title = Column(String(225), nullable=True, comment='会议主题')
    meeting_date = Column(Integer, nullable=False, server_default='0', comment='会议时间')
    room_id = Column(Integer, nullable=False, server_default='0', comment='会议室')
    did = Column(Integer, nullable=False, server_default='0', comment='主办部门')
    content = Column(Text, nullable=False, comment='会议内容')
    plans = Column(Text, nullable=False, comment='下一步实施计划')
    file_ids = Column(String(500), nullable=False, server_default="''", comment='相关附件')
    join_uids = Column(String(500), nullable=False, server_default="''", comment='与会人员')
    sign_uids = Column(String(500), nullable=False, server_default="''", comment='签到人员')
    share_uids = Column(String(500), nullable=False, server_default="''", comment='共享给谁')
    anchor_id = Column(Integer, nullable=False, server_default='0', comment='主持人 id')
    recorder_id = Column(Integer, nullable=False, server_default='0', comment='记录人 id')
    remarks = Column(Text, nullable=False, comment='备注内容')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='发布人 id')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')
