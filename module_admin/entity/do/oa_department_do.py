from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String

from config.database import Base


class OaDepartment(Base):
    """
    部门组织表
    """

    __tablename__ = 'oa_department'
    __table_args__ = {'comment': '部门组织'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='ID')
    title = Column(String(100), nullable=False, server_default='', comment='部门名称')
    pid = Column(Integer, nullable=False, server_default='0', comment='上级部门id')
    leader_ids = Column(String(500), nullable=True, server_default='', comment='部门负责人ids')
    phone = Column(String(60), nullable=False, server_default='', comment='部门联系电话')
    sort = Column(Integer, nullable=False, server_default='0', comment='排序：越大越靠前')
    remark = Column(String(1000), nullable=True, server_default='', comment='备注')
    status = Column(SmallInteger, nullable=False, server_default='1', comment='状态：-1删除 0禁用 1启用')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
