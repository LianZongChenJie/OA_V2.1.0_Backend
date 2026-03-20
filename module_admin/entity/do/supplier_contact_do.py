from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Boolean


class OaSupplierContact(Base):
    """供应商联系人表实体类"""

    __tablename__ = 'oa_supplier_contact'
    __table_args__ = {'comment': '供应商联系人表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    name = Column(String(100), nullable=False, default='', comment='联系人姓名')
    mobile = Column(String(20), nullable=False, default='', comment='联系电话')
    sex = Column(String(10), nullable=False, default='', comment='性别')
    sid = Column(Integer, nullable=False, default=0, comment='供应商 ID')
    is_default = Column(SmallInteger, nullable=False, default=0, comment='是否默认联系人：0 否 1 是')

    # 管理信息
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')

    # 状态
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1 删除 0 禁用 1 启用')

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
            'name': self.name,
            'mobile': self.mobile,
            'sex': self.sex,
            'sid': self.sid,
            'is_default': self.is_default,
            'admin_id': self.admin_id,
            'status': self.status,
            'create_time': self.create_time,
            'update_time': self.update_time,
            'delete_time': self.delete_time
        }
