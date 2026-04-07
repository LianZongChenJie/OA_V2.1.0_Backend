from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Boolean


class OaSupplierContact(Base):
    """供应商联系人表实体类"""

    __tablename__ = 'oa_supplier_contact'
    __table_args__ = {'comment': '供应商联系人表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    sid = Column(Integer, nullable=False, default=0, comment='供应商 ID')
    is_default = Column(SmallInteger, nullable=False, default=0, comment='是否是第一联系人')
    name = Column(String(100), nullable=False, default='', comment='姓名')
    sex = Column(SmallInteger, nullable=False, default=0, comment='用户性别:0 未知，1 男，2 女')
    mobile = Column(String(20), nullable=False, default='', comment='手机号码')
    qq = Column(String(20), nullable=False, default='', comment='QQ 号')
    wechat = Column(String(100), nullable=False, default='', comment='微信号')
    email = Column(String(100), nullable=False, default='', comment='邮件地址')
    nickname = Column(String(50), nullable=False, default='', comment='称谓')
    department = Column(String(50), nullable=False, default='', comment='部门')
    position = Column(String(50), nullable=False, default='', comment='职务')

    # 管理信息
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def __repr__(self) -> str:
        return f"<OaSupplierContact(id={self.id}, name='{self.name}', sid={self.sid})>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'sid': self.sid,
            'is_default': self.is_default,
            'name': self.name,
            'sex': self.sex,
            'mobile': self.mobile,
            'qq': self.qq,
            'wechat': self.wechat,
            'email': self.email,
            'nickname': self.nickname,
            'department': self.department,
            'position': self.position,
            'admin_id': self.admin_id,
            'create_time': self.create_time,
            'update_time': self.update_time,
            'delete_time': self.delete_time
        }
