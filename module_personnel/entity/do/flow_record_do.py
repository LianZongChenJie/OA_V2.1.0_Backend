from config.database import Base
from sqlalchemy import Column, Integer, String, SmallInteger, BigInteger
class OaFlowRecord(Base):
    """审批记录表实体类"""

    __tablename__ = 'oa_flow_record'
    __table_args__ = {'comment': '审批记录表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 审批内容
    action_id = Column(Integer, nullable=False, default=0, comment='审批内容ID')
    check_table = Column(String(255), nullable=False, default='审批数据表', comment='审批数据表')

    # 流程信息
    flow_id = Column(Integer, nullable=False, comment='审批模版流程id')
    step_id = Column(Integer, nullable=False, default=0, comment='审批步骤ID')

    # 审批附件
    check_files = Column(String(500), nullable=False, default='', comment='审批附件')

    # 审批人信息
    check_uid = Column(Integer, nullable=False, default=0, comment='审批人ID')
    check_time = Column(BigInteger, nullable=False, comment='审批时间')

    # 审批状态
    check_status = Column(SmallInteger, nullable=False, default=0, comment='审批状态:0发起,1通过,2拒绝,3撤销')
    content = Column(String(500), nullable=False, default='', comment='审批意见')

    # 删除时间
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}