from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger
from config.database import Base

class OaEnterprise(Base):
    """企业主体实体类"""

    __tablename__ = 'oa_enterprise'
    __table_args__ = {'comment': '企业主体'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 企业基本信息
    title = Column(String(100), nullable=False, default='', comment='企业名称')
    city = Column(String(60), nullable=False, default='', comment='所在城市')

    # 银行信息
    bank = Column(String(60), nullable=False, default='', comment='开户银行')
    bank_sn = Column(String(60), nullable=False, default='', comment='银行帐号')

    # 开票信息
    tax_num = Column(String(100), nullable=False, default='', comment='纳税人识别号')
    phone = Column(String(20), nullable=False, default='', comment='开票电话')
    address = Column(String(200), nullable=False, default='', comment='开票地址')

    # 其他信息
    remark = Column(String(500), nullable=False, default='', comment='备注说明')
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：-1删除 0禁用 1启用')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')


    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}