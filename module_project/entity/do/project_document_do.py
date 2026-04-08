from config.database import Base
from sqlalchemy import Column, Integer, String, Text, BigInteger


class OaProjectDocument(Base):
    """项目文档表实体类"""

    __tablename__ = 'oa_project_document'
    __table_args__ = {'comment': '项目文档表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    project_id = Column(Integer, nullable=False, default=0, comment='关联项目id')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    title = Column(String(255), nullable=False, default='', comment='标题')
    did = Column(Integer, nullable=False, default=0, comment='所属部门')
    file_ids = Column(String(500), nullable=False, default='', comment='附件ids')
    content = Column(Text, comment='文档内容')
    md_content = Column(Text, comment='markdown文档内容')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='添加时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='修改时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def __repr__(self) -> str:
        return f"<OaProjectDocument(id={self.id}, title='{self.title}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'admin_id': self.admin_id,
            'title': self.title,
            'did': self.did,
            'file_ids': self.file_ids,
            'content': self.content,
            'md_content': self.md_content,
            'create_time': self.create_time,
            'update_time': self.update_time,
            'delete_time': self.delete_time
        }
