from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text
from config.database import Base

class OaSeal(Base):
    """用章申请表实体类"""
    __tablename__ = 'oa_seal'
    __table_args__ = {'comment': '用章申请表', 'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    title = Column(String(255), nullable=False, default='', comment='用章申请主题')
    seal_cate_id = Column(Integer, nullable=False, default=0, comment='印章类型')
    content = Column(Text, nullable=True, comment='盖章内容')
    file_ids = Column(String(255), nullable=False, default='', comment='附件ids,如:1,2,3')
    did = Column(Integer, nullable=False, default=0, comment='用印部门')
    num = Column(Integer, nullable=False, default=0, comment='盖章次数')
    use_time = Column(BigInteger, nullable=False, default=0, comment='预期用印日期')
    is_borrow = Column(SmallInteger, nullable=False, default=0, comment='印章是否外借:0,1')
    start_time = Column(BigInteger, nullable=False, default=0, comment='印章借用日期')
    end_time = Column(BigInteger, nullable=False, default=0, comment='结束借用日期')
    status = Column(SmallInteger, nullable=False, default=0, comment='状态:0待使用,1已使用(已外借),2已结束归还')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    check_status = Column(SmallInteger, nullable=False, default=0, comment='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id = Column(Integer, nullable=False, default=0, comment='审核流程id')
    check_step_sort = Column(Integer, nullable=False, default=0, comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, default='', comment='当前审批人ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, default='', comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, default='', comment='历史审批人ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, default='', comment='抄送人ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, default=0, comment='审核通过时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}