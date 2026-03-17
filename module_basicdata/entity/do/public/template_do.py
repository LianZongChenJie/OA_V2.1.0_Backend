# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String,SmallInteger,BigInteger

from config.database import Base


class OaTemplate(Base):
    """消息模板表"""
    __tablename__ = 'oa_template'
    __table_args__ = {'comment': '消息模板表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    title = Column(String(255), nullable=False, default='', comment='消息模板名称')
    name = Column(String(255), nullable=False, default='', comment='权限标识唯一')
    types = Column(SmallInteger, nullable=False, default=1, comment='类型:1普通消息,2审批消息')
    check_types = Column(Integer, nullable=False, default=0, comment='审批类型:0')
    remark = Column(String(500), nullable=False, default='', comment='备注描述，使用场景等')
    msg_link = Column(String(255), nullable=False, default='', comment='消息模板链接(审批申请)')
    msg_title_0 = Column(String(255), nullable=False, default='', comment='消息模板标题(审批申请发审批人)')
    msg_content_0 = Column(String(500), nullable=False, default='', comment='消息模板内容(审批申请发审批人)')
    msg_title_1 = Column(String(255), nullable=False, default='', comment='消息模板标题(审批通过发申请人)')
    msg_content_1 = Column(String(500), nullable=False, default='', comment='消息模板内容(审批通过发申请人)')
    msg_title_2 = Column(String(255), nullable=False, default='', comment='消息模板标题(审批拒绝发申请人)')
    msg_content_2 = Column(String(500), nullable=False, default='', comment='消息模板内容(审批拒绝发申请人)')
    msg_title_3 = Column(String(255), nullable=False, default='', comment='消息模板标题(审批通过发抄送人)')
    msg_content_3 = Column(String(500), nullable=False, default='', comment='消息模板内容(审批通过发抄送人)')
    email_link = Column(String(255), nullable=False, default='', comment='邮箱消息模板链接')
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1删除 0禁用 1启用')
    admin_id = Column(String, nullable=False, default=0, comment='创建人')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'name': self.name,
            'types': self.types,
            'check_types': self.check_types,
            'remark': self.remark,
            'msg_link': self.msg_link,
            'msg_title_0': self.msg_title_0,
            'msg_content_0': self.msg_content_0,
            'msg_title_1': self.msg_title_1,
            'msg_content_1': self.msg_content_1,
            'msg_title_2': self.msg_title_2,
            'msg_content_2': self.msg_content_2,
            'msg_title_3': self.msg_title_3,
            'msg_content_3': self.msg_content_3,
            'email_link': self.email_link,
            'status': self.status,
            'admin_id': self.admin_id,
            'create_time': self.create_time,
            'update_time': self.update_time,
            'delete_time': self.delete_time
        }