from sqlalchemy import Column, Integer, String, Text, BigInteger, DECIMAL, SmallInteger

from config.database import Base


class OaProjectTask(Base):
    """
    项目任务表
    """
    __tablename__ = 'oa_project_task'
    __table_args__ = {'comment': '项目任务'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='任务 ID')
    title = Column(String(255), nullable=False, default='', comment='主题')
    pid = Column(Integer, nullable=False, default=0, comment='父级任务 id')
    before_task = Column(Integer, nullable=False, default=0, comment='前置任务 id')
    project_id = Column(Integer, nullable=False, default=0, comment='关联项目 id')
    work_id = Column(Integer, nullable=False, default=0, comment='关联工作类型')
    step_id = Column(Integer, nullable=False, default=0, comment='关联项目阶段')
    plan_hours = Column(DECIMAL(10, 1), nullable=False, default=0.0, comment='预估工时')
    end_time = Column(BigInteger, nullable=False, default=0, comment='预计结束时间')
    over_time = Column(BigInteger, nullable=False, default=0, comment='实际结束时间')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    director_uid = Column(Integer, nullable=False, default=0, comment='指派给 (负责人)')
    did = Column(Integer, nullable=False, default=0, comment='所属部门')
    assist_admin_ids = Column(String(500), nullable=False, default='', comment='协助人员，如:1,2,3')
    priority = Column(SmallInteger, nullable=False, default=1, comment='优先级:1 低，2 中，3 高，4 紧急')
    status = Column(SmallInteger, nullable=False, default=1, comment='任务状态：1 待办的，2 进行中，3 已完成，4 已拒绝，5 已关闭')
    done_ratio = Column(Integer, nullable=False, default=0, comment='完成进度：0,20,40,50,60,80')
    content = Column(Text, comment='任务描述')
    create_time = Column(BigInteger, nullable=False, default=0, comment='添加时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='修改时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
