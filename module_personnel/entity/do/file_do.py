from config.database import Base
from sqlalchemy import Column, Integer, String, SmallInteger, Text, BigInteger

class OaFile(Base):
    """文件实体类"""

    __tablename__ = 'oa_file'
    __table_args__ = {'comment': '文件表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 文件信息
    module = Column(String(20), nullable=False, default='', comment='所属模块')
    sha1 = Column(String(60), nullable=False, comment='sha1')
    md5 = Column(String(60), nullable=False, comment='md5')
    name = Column(String(255), nullable=False, default='', comment='原始文件名')
    filename = Column(String(255), nullable=False, default='', comment='文件名')
    filepath = Column(String(255), nullable=False, default='', comment='文件路径+文件名')
    thumbpath = Column(String(255), nullable=False, default='', comment='缩略图路径')
    filesize = Column(Integer, nullable=False, default=0, comment='文件大小')
    fileext = Column(String(10), nullable=False, default='', comment='文件后缀')
    mimetype = Column(String(100), nullable=False, default='', comment='文件类型')

    # 关联信息
    group_id = Column(Integer, nullable=False, default=0, comment='文件分组ID')
    user_id = Column(Integer, nullable=False, default=0, comment='上传会员ID')
    admin_id = Column(Integer, nullable=False, comment='审核者id')

    # 状态信息
    status = Column(SmallInteger, nullable=False, default=0, comment='0未审核1已审核-1不通过')
    download = Column(Integer, nullable=False, default=0, comment='下载量')

    # 其他信息
    uploadip = Column(String(64), nullable=False, default='', comment='上传IP')
    action = Column(String(50), nullable=False, default='', comment='来源模块功能')
    use = Column(String(255), nullable=True, comment='用处')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    audit_time = Column(BigInteger, nullable=False, default=0, comment='审核时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
