from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger

class OaFlowStep(Base):
    """审批步骤表实体类"""

    __tablename__ = 'oa_flow_step'
    __table_args__ = {'comment': '审批步骤表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    flow_name = Column(String(255), nullable=False, default='', comment='流程步骤名称')
    action_id = Column(Integer, nullable=False, comment='审批内容ID')
    flow_id = Column(Integer, nullable=False, comment='审批流程id')

    # 审批角色配置
    check_role = Column(SmallInteger, nullable=False, default=0, comment='审批角色:0自由指定,1当前部门负责人,2上一级部门负责人,3指定职位,4指定用户,5可回退审批')
    check_position_id = Column(Integer, nullable=False, default=0, comment='审批角色id')
    check_uids = Column(String(500), nullable=False, default='', comment='审批人ids(1,2,3)')

    # 审批方式
    check_types = Column(SmallInteger, nullable=False, default=1, comment='审批方式:1会签2或签')

    # 排序
    sort = Column(SmallInteger, nullable=False, default=0, comment='排序ID')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}