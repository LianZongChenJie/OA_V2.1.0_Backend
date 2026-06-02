# module_personnel/entity/do/social_security_do.py
from sqlalchemy import Column, Integer, String, BigInteger, Text
from config.database import Base


class OaSocialSecurity(Base):
    """社保信息表实体类"""

    __tablename__ = 'oa_social_security'
    __table_args__ = {'comment': '社保信息表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    city = Column(String(100), nullable=False, default='', comment='所在城市')
    city_id = Column(String(255), nullable=False, default='', comment='城市ID(多ID逗号分隔)')
    project_name = Column(String(255), nullable=False, default='', comment='项目名称')
    social_date = Column(Integer, nullable=False, default=15, comment='社保日期(每月几号)')
    remark = Column(Text, nullable=True, comment='备注')

    # 创建人信息
    create_by = Column(String(100), nullable=False, default='', comment='创建人')
    create_by_id = Column(Integer, nullable=False, default=0, comment='创建人ID')

    # 负责人信息
    manager = Column(String(100), nullable=False, default='', comment='负责人')
    manager_id = Column(Integer, nullable=False, default=0, comment='负责人ID')

    # 状态
    status = Column(Integer, nullable=False, default=1, comment='状态：1正常，0终止')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class OaSocialSecurityUser(Base):
    """社保关联人员表实体类"""

    __tablename__ = 'oa_social_security_user'
    __table_args__ = {'comment': '社保关联人员表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 关联信息
    social_id = Column(Integer, nullable=False, default=0, comment='社保信息ID')
    user_id = Column(Integer, nullable=False, default=0, comment='员工ID')

    # 状态
    status = Column(Integer, nullable=False, default=1, comment='状态：1参保，0减员')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}