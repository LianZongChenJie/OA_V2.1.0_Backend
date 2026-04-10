from sqlalchemy import BigInteger, Column, Integer

from config.database import Base


class OaDepartmentAdmin(Base):
    """
    次要部门人员关联表
    """

    __tablename__ = 'oa_department_admin'
    __table_args__ = {'comment': '次要部门人员关联表'}

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='ID')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='员工ID')
    department_id = Column(Integer, nullable=False, server_default='0', comment='部门ID')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
