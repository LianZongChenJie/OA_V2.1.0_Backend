from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text
from config.database import Base
from sqlalchemy import Index
class OaMessage(Base):
    """发消息表实体类"""

    __tablename__ = 'oa_message'
    __table_args__ = (
        Index('idx_from_uid', 'from_uid'),
        Index('idx_create_time', 'create_time'),
        Index('idx_send_time', 'send_time'),
        Index('idx_types', 'types'),
        Index('idx_is_draft', 'is_draft'),
        {'comment': '发消息表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    title = Column(String(100), nullable=False, default='', comment='消息主题')
    template = Column(String(100), nullable=False, default='', comment='消息模板,默认是空私人消息,其他则在配置文件查看消息模板')
    content = Column(Text, nullable=True, comment='消息内容')
    file_ids = Column(Text, nullable=True, comment='消息附件')
    from_uid = Column(Integer, nullable=False, default=0, comment='发送人id，0为系统消息')
    types = Column(SmallInteger, nullable=True, default=0, comment='接收人类型：1人员,2部门,3岗位,4全部')
    uids = Column(String(500), nullable=False, default='', comment='人员ids')
    dids = Column(String(500), nullable=False, default='', comment='部门ids')
    pids = Column(String(500), nullable=False, default='', comment='岗位ids')
    copy_uids = Column(String(500), nullable=False, default='', comment='抄送人员ids')
    msg_id = Column(Integer, nullable=False, default=0, comment='转发、回复关联消息id')
    is_draft = Column(SmallInteger, nullable=False, default=1, comment='是否是草稿：1正常消息 2草稿消息')
    send_time = Column(BigInteger, nullable=False, default=0, comment='发送日期')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    clear_time = Column(BigInteger, nullable=False, default=0, comment='清除时间')
    action_id = Column(Integer, nullable=False, default=0, comment='操作模块数据的id（针对系统消息）')

    def to_dict(self):
        """转换为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}