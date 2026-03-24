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
    title = Column(String(100), nullable=False, server_default="''", comment='预定主题')
    start_date = Column(BigInteger, nullable=False, server_default='0', comment='开始时间')
    end_date = Column(BigInteger, nullable=False, server_default='0', comment='结束时间')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='预定人 ID')
    did = Column(Integer, nullable=False, server_default='0', comment='部门 ID')
    requirements = Column(String(255), nullable=False, server_default="''", comment='会议要求')
    check_status = Column(SmallInteger, nullable=False, server_default='1', comment='审核状态：1 待审核 2 通过 3 拒绝')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')


class OaMeetingRecords(Base):
    """
    会议纪要表
    """
    __tablename__ = 'oa_meeting_records'
    __table_args__ = {'comment': '会议纪要'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    order_id = Column(Integer, nullable=False, server_default='0', comment='预定订单 ID')
    title = Column(String(100), nullable=False, server_default="''", comment='会议主题')
    meeting_date = Column(BigInteger, nullable=False, server_default='0', comment='会议日期')
    anchor_id = Column(Integer, nullable=False, server_default='0', comment='主持人 ID')
    recorder_id = Column(Integer, nullable=False, server_default='0', comment='记录人 ID')
    content = Column(Text, nullable=True, comment='会议内容')
    file_ids = Column(String(500), nullable=False, server_default="''", comment='附件 ID')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='创建人 ID')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')
