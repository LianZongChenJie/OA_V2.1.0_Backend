from config.database import Base
from sqlalchemy import Column, Integer, String, SmallInteger, BigInteger

from pydantic import field_serializer
from typing import Optional

class OaDepartmentChange(Base):
    """人事调动申请表实体类"""

    __tablename__ = 'oa_department_change'
    __table_args__ = {'comment': '人事调动申请表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 员工信息
    uid = Column(Integer, nullable=False, default=0, comment='员工ID')
    from_did = Column(Integer, nullable=False, default=0, comment='原部门id')
    to_did = Column(Integer, nullable=False, default=0, comment='调到部门id')

    # 交接信息
    connect_id = Column(Integer, nullable=False, default=0, comment='资料交接人')
    connect_time = Column(BigInteger, nullable=False, default=0, comment='资料交接时间')
    connect_uids = Column(String(100), nullable=False, default='', comment='参与交接人,可多个')
    file_ids = Column(String(500), nullable=False, default='', comment='档案附件')

    # 调动信息
    move_time = Column(BigInteger, nullable=False, default=0, comment='调动时间')
    status = Column(Integer, nullable=False, default=1, comment='状态:1未调动,2已交接调动')
    remark = Column(String(1000), default='', comment='备注信息')

    # 创建人信息
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    did = Column(Integer, nullable=False, default=0, comment='创建人所在部门')

    # 审核信息
    check_status = Column(SmallInteger, nullable=False, default=0,
                          comment='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id = Column(Integer, nullable=False, default=0, comment='审核流程id')
    check_step_sort = Column(Integer, nullable=False, default=0, comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, default='', comment='当前审批人ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, default='', comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, default='', comment='历史审批人ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, default='', comment='抄送人ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, default=0, comment='审核通过时间')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}