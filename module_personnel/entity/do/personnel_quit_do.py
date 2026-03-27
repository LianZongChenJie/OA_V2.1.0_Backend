from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, BigInteger, SmallInteger
from typing import Optional
from config.database import Base
class OaPersonalQuit(Base):
    """离职申请表实体类（SQLAlchemy 2.0 风格）"""
    __tablename__ = 'oa_personal_quit'
    __table_args__ = {'comment': '离职申请表'}
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    uid: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='用户ID')
    lead_admin_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='上级领导')
    connect_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='资料交接人')
    connect_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='资料交接时间')
    connect_uids: Mapped[str] = mapped_column(String(100), nullable=False, default='', comment='参与交接人,可多个')
    file_ids: Mapped[str] = mapped_column(String(500), nullable=False, default='', comment='档案附件')
    quit_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='离职时间')
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment='状态:1未交接,2已交接离职')
    remark: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, default='', comment='备注信息')
    admin_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='创建人')
    did: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='创建人所在部门')
    check_status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, comment='审核状态')
    check_flow_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='审核流程id')
    check_step_sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='当前审批步骤')
    check_uids: Mapped[str] = mapped_column(String(500), nullable=False, default='', comment='当前审批人ID')
    check_last_uid: Mapped[str] = mapped_column(String(500), nullable=False, default='', comment='上一审批人')
    check_history_uids: Mapped[str] = mapped_column(String(500), nullable=False, default='', comment='历史审批人ID')
    check_copy_uids: Mapped[str] = mapped_column(String(500), nullable=False, default='', comment='抄送人ID')
    check_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='审核通过时间')
    create_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}