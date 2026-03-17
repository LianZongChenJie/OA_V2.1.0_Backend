from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Boolean

class OaFlowCate(Base):
    """审批类型实体类"""

    __tablename__ = 'oa_flow_cate'
    __table_args__ = {'comment': '审批类型'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    title = Column(String(100), nullable=False, default='', comment='审批类型名称')
    name = Column(String(100), nullable=False, comment='审批类型标识,唯一')
    module_id = Column(Integer, nullable=False, default=0, comment='关联审批模块id')
    check_table = Column(String(100), nullable=False, default='', comment='关联数据库表名')
    icon = Column(String(255), nullable=False, default='', comment='图标')

    # 权限与排序
    department_ids = Column(String(255), nullable=False, default='', comment='应用部门ID（空为全部）1,2,3')
    sort = Column(Integer, nullable=False, default=0, comment='排序：越大越靠前')

    # 功能配置
    is_copy = Column(Integer, nullable=False, default=1, comment='是否支持抄送人')
    is_file = Column(Integer, nullable=False, default=0, comment='审批过程是否支持上传附件')
    is_export = Column(Integer, nullable=False, default=0, comment='审批通过后是否支持导出PDF打印')
    is_back = Column(Integer, nullable=False, default=1, comment='是否支持撤回')
    is_reversed = Column(Integer, nullable=False, default=0, comment='是否支持反确认')

    # 表单配置
    form = Column(Boolean, nullable=False, default=1, comment='预设字段，表单模式：1固定表单,2自定义表单')
    add_url = Column(String(255), nullable=False, default='', comment='新建链接：固定表单模式必填')
    view_url = Column(String(255), nullable=False, default='', comment='查看链接：固定表单模式必填')
    form_id = Column(Integer, nullable=False, default=0, comment='表单id：自定义表单模式必填')

    # 显示与状态
    is_list = Column(Boolean, nullable=False, default=1, comment='是否列表页显示：0不显示 1显示')
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1删除 0禁用 1启用')
    template_id = Column(Integer, nullable=False, default=0, comment='审批消息模板id')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def __repr__(self) -> str:
        return f"<OaFlowCate(id={self.id}, title='{self.title}', name='{self.name}')>"


    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'name': self.name,
            'module_id': self.module_id,
            'check_table': self.check_table,
            'icon': self.icon,
            'department_ids': self.department_ids,
            'sort': self.sort,
            'is_copy': self.is_copy,
            'is_file': self.is_file,
            'is_export': self.is_export,
            'is_back': self.is_back,
            'is_reversed': self.is_reversed,
            'form': self.form,
            'add_url': self.add_url,
            'view_url': self.view_url,
            'form_id': self.form_id,
            'is_list': self.is_list,
            'status': self.status,
            'template_id': self.template_id,
            'create_time': self.create_time,
            'update_time': self.update_time
        }