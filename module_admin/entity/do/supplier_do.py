from config.database import Base
from sqlalchemy import Column, Integer, String, Numeric, Text, BigInteger, SmallInteger


class OaSupplier(Base):
    """供应商表实体类"""

    __tablename__ = 'oa_supplier'
    __table_args__ = {'comment': '供应商表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    title = Column(String(255), nullable=False, default='', comment='供应商名称')
    code = Column(String(255), nullable=False, default='', comment='供应商编号')
    phone = Column(String(255), nullable=False, default='', comment='供应商电话')
    email = Column(String(255), nullable=False, default='', comment='供应商邮箱')
    address = Column(String(255), nullable=False, default='', comment='供应商联系地址')
    file_ids = Column(String(255), nullable=False, default='', comment='附件 ids，如:1,2,3')
    products = Column(String(500), nullable=False, default='', comment='供应商商品')
    content = Column(Text, comment='供应商描述')

    # 税务信息
    tax_num = Column(String(100), nullable=False, default='', comment='纳税人识别号')
    tax_mobile = Column(String(20), nullable=False, default='', comment='开票电话')
    tax_address = Column(String(200), nullable=False, default='', comment='开票地址')
    tax_bank = Column(String(60), nullable=False, default='', comment='开户银行')
    tax_banksn = Column(String(60), nullable=False, default='', comment='银行帐号')

    # 资质附件
    file_license_ids = Column(String(500), nullable=False, default='', comment='营业执照附件，如:1,2,3')
    file_idcard_ids = Column(String(500), nullable=False, default='', comment='身份证附件，如:1,2,3')
    file_bankcard_ids = Column(String(500), nullable=False, default='', comment='银行卡附件，如:1,2,3')
    file_openbank_ids = Column(String(500), nullable=False, default='', comment='开户行附件，如:1,2,3')

    # 税率
    tax_rate = Column(Numeric(15, 2), nullable=False, default=0.00, comment='税率')

    # 管理信息
    admin_id = Column(Integer, nullable=False, default=0, comment='录入人')
    sort = Column(Integer, nullable=False, default=0, comment='排序')

    # 状态
    status = Column(SmallInteger, nullable=False, default=1, comment='供应商状态：0 禁用，1 启用')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='添加时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='修改时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def __repr__(self) -> str:
        return f"<OaSupplier(id={self.id}, title='{self.title}', code='{self.code}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'code': self.code,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'file_ids': self.file_ids,
            'products': self.products,
            'content': self.content,
            'status': self.status,
            'tax_num': self.tax_num,
            'tax_mobile': self.tax_mobile,
            'tax_address': self.tax_address,
            'tax_bank': self.tax_bank,
            'tax_banksn': self.tax_banksn,
            'file_license_ids': self.file_license_ids,
            'file_idcard_ids': self.file_idcard_ids,
            'file_bankcard_ids': self.file_bankcard_ids,
            'file_openbank_ids': self.file_openbank_ids,
            'tax_rate': float(self.tax_rate) if self.tax_rate else 0.00,
            'admin_id': self.admin_id,
            'sort': self.sort,
            'create_time': self.create_time,
            'update_time': self.update_time,
            'delete_time': self.delete_time
        }
