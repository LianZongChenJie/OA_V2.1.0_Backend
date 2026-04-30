from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text
from config.database import Base
from sqlalchemy import Index
class OaMsg(Base):
    """消息表实体类"""

    __tablename__ = 'oa_msg'
    __table_args__ = (
        Index('idx_from_uid', 'from_uid'),
        Index('idx_to_uid', 'to_uid'),
        Index('idx_create_time', 'create_time'),
        Index('idx_message_id', 'message_id'),
        Index('idx_msg_id', 'msg_id'),
        {'comment': '消息表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    title = Column(String(100), nullable=False, default='', comment='消息主题')
    template = Column(String(100), nullable=False, default='', comment='消息模板,默认是私人文本消息,其他则在配置文件查看消息模板')
    content = Column(Text, nullable=True, comment='消息内容')
    file_ids = Column(Text, nullable=True, comment='消息附件')
    from_uid = Column(Integer, nullable=False, default=0, comment='发送人id，0为系统消息')
    to_uid = Column(Integer, nullable=False, default=0, comment='接收人id')
    message_id = Column(Integer, nullable=False, default=0, comment='来源发件消息id,0为系统消息')
    msg_id = Column(Integer, nullable=False, default=0, comment='转发、回复关联消息id')
    is_star = Column(SmallInteger, nullable=False, default=0, comment='是否星标信息：1是 0不是')
    read_time = Column(BigInteger, nullable=False, default=0, comment='阅读时间')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    clear_time = Column(BigInteger, nullable=False, default=0, comment='清除时间')
    action_id = Column(Integer, nullable=False, default=0, comment='操作模块数据的id（针对系统消息）')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}