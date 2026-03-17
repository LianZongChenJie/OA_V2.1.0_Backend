from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger


class FlowModule(Base):
    __tablename__ = "oa_flow_module"
    __table_args__ = {"comment": "审批模块"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False, default='', comment='审批模块名称')
    icon = Column(String(255), nullable=False, default='', comment='预设字段，图标')
    sort = Column(Integer, nullable=False, default=0, comment='排序：越大越靠前')
    department_ids = Column(String(255), nullable=False, default='', comment='应用部门ID（空为全部）1,2,3')
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1删除 0禁用 1启用')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'icon': self.icon,
            'sort': self.sort,
            'department_ids': self.department_ids,
            'status': self.status,
            'create_time': self.create_time,
            'update_time': self.update_time
        }
