from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text
from config.database import Base
from sqlalchemy import Index


class OaNote(Base):
    """公告表实体类"""

    __tablename__ = 'oa_note'
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_cate_id', 'cate_id'),
        Index('idx_start_end_time', 'start_time', 'end_time'),
        Index('idx_create_time', 'create_time'),
        {'comment': '公告表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    cate_id = Column(Integer, nullable=False, default=0, comment='公告分类ID')
    sourse = Column(SmallInteger, nullable=False, default=1, comment='发布平台:1PC,2手机')
    title = Column(String(225), nullable=True, comment='标题')
    content = Column(Text, nullable=False, comment='公告内容')
    src = Column(String(100), nullable=True, comment='关联链接')
    status = Column(Integer, nullable=False, default=1, comment='1可用-1禁用')
    sort = Column(Integer, nullable=False, default=0, comment='排序')
    file_ids = Column(String(500), nullable=False, default='', comment='相关附件')
    role_type = Column(SmallInteger, nullable=False, default=0, comment='查看权限，0所有人,1部门,2人员')
    role_dids = Column(String(500), nullable=False, default='', comment='可查看部门')
    role_uids = Column(String(500), nullable=False, default='', comment='可查看用户')
    start_time = Column(BigInteger, nullable=False, default=0, comment='展示开始时间')
    end_time = Column(BigInteger, nullable=False, default=0, comment='展示结束时间')
    admin_id = Column(Integer, nullable=False, default=0, comment='发布人id')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}