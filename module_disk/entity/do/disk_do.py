"""
网盘文件表实体类
"""
from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger


class OaDisk(Base):
    """网盘文件表实体类"""

    __tablename__ = 'oa_disk'
    __table_args__ = {'comment': '网盘文件表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    pid = Column(Integer, nullable=False, default=0, comment='所在文件夹目录ID')
    did = Column(Integer, nullable=False, default=0, comment='所属部门')
    types = Column(SmallInteger, nullable=False, default=0, comment='类型:0文件,1在线文档,2文件夹')
    action_id = Column(Integer, nullable=False, default=0, comment='相关联id')
    group_id = Column(Integer, nullable=False, default=0, comment='分享空间id')
    name = Column(String(200), nullable=False, default='', comment='文件名称')
    file_ext = Column(String(200), nullable=False, default='', comment='文件后缀名称')
    file_size = Column(BigInteger, nullable=False, default=0, comment='文件大小')
    is_star = Column(SmallInteger, nullable=False, default=0, comment='重要与否')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='修改时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    clear_time = Column(BigInteger, nullable=False, default=0, comment='清除时间')

    def __repr__(self) -> str:
        return f"<OaDisk(id={self.id}, name='{self.name}', types={self.types})>"
