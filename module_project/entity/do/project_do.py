from sqlalchemy import Column, Integer, String, Text, DECIMAL
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class OaProject(Base):
    """
    项目表数据库模型
    """
    __tablename__ = 'oa_project'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='项目 ID')
    name = Column(String(255), nullable=False, default='', comment='项目名称')
    code = Column(String(255), nullable=False, default='', comment='项目编号')
    amount = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment='项目金额')
    cate_id = Column(Integer, nullable=False, default=0, comment='分类 ID')
    customer_id = Column(Integer, nullable=False, default=0, comment='关联客户 ID')
    contract_id = Column(Integer, nullable=False, default=0, comment='关联合同协议 ID')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    director_uid = Column(Integer, nullable=False, default=0, comment='项目负责人')
    did = Column(Integer, nullable=False, default=0, comment='项目所属部门')
    start_time = Column(Integer, nullable=False, default=0, comment='项目开始时间')
    end_time = Column(Integer, nullable=False, default=0, comment='项目结束时间')
    status = Column(Integer, nullable=False, default=1, comment='状态：0 未设置，1 未开始，2 进行中，3 已完成，4 已关闭')
    content = Column(Text, comment='项目描述')
    create_time = Column(Integer, nullable=False, default=0, comment='添加时间')
    update_time = Column(Integer, nullable=False, default=0, comment='修改时间')
    delete_time = Column(Integer, nullable=False, default=0, comment='删除时间')
