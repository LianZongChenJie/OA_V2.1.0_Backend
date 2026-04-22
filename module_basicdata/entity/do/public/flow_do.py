from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Boolean
class OaFlow(Base):
    """审批流程实体类"""
    __tablename__ = 'oa_flow'
    __table_args__ = {'comment': '审批流程'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    title = Column(String(50), nullable=False, default='', comment='审批流程名称')
    cate_id = Column(SmallInteger, nullable=False, default=0, comment='关联审批类型id')
    check_type = Column(SmallInteger, nullable=False,
                        comment='1自由审批流,2固定审批流,3固定可回退的审批流,4固定条件审批流')

    # 权限配置
    department_ids = Column(String(500), nullable=False, default='', comment='应用部门ID（0为全部）1,2,3')
    copy_uids = Column(String(500), nullable=False, default='', comment='抄送人ID')

    # 流程配置
    flow_list = Column(String(1000), default='', comment='流程数据序列化')

    # 状态信息
    status = Column(SmallInteger, nullable=False, default=1, comment='状态 1启用，0禁用')
    remark = Column(String(500), nullable=False, default='', comment='流程说明')
    admin_id = Column(Integer, nullable=False, comment='创建人ID')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
