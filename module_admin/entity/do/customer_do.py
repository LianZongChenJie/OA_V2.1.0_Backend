from sqlalchemy import BigInteger, Column, Integer, String, Text

from config.database import Base


class OaCustomer(Base):
    """
    客户表
    """

    __tablename__ = 'oa_customer'
    __table_args__ = {'comment': '客户表'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='客户 ID')
    name = Column(String(255), nullable=False, server_default="''", comment='客户名称')
    source_id = Column(Integer, nullable=False, server_default='0', comment='客户来源 id')
    grade_id = Column(Integer, nullable=False, server_default='0', comment='客户等级 id')
    industry_id = Column(Integer, nullable=False, server_default='0', comment='所属行业 id')
    services_id = Column(Integer, nullable=False, server_default='0', comment='客户意向 id')
    provinceid = Column(Integer, nullable=False, server_default='0', comment='省份 id')
    cityid = Column(Integer, nullable=False, server_default='0', comment='城市 id')
    distid = Column(Integer, nullable=False, server_default='0', comment='区县 id')
    townid = Column(BigInteger, nullable=False, server_default='0', comment='城镇 id')
    address = Column(String(255), nullable=False, server_default="''", comment='客户联系地址')
    customer_status = Column(Integer, nullable=False, server_default='0', comment='客户状态：0 未设置')
    intent_status = Column(Integer, nullable=False, server_default='0', comment='意向状态：0 未设置')
    contact_first = Column(Integer, nullable=False, server_default='0', comment='第一联系人 id')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='录入人')
    belong_uid = Column(Integer, nullable=False, server_default='0', comment='所属人')
    belong_did = Column(Integer, nullable=False, server_default='0', comment='所属部门')
    belong_time = Column(BigInteger, nullable=False, server_default='0', comment='获取时间')
    distribute_time = Column(BigInteger, nullable=False, server_default='0', comment='最新分配时间')
    follow_time = Column(BigInteger, nullable=False, server_default='0', comment='最新跟进时间')
    next_time = Column(BigInteger, nullable=False, server_default='0', comment='下次跟进时间')
    discard_time = Column(BigInteger, nullable=False, server_default='0', comment='废弃时间')
    share_ids = Column(String(500), nullable=False, server_default="''", comment='共享人员，如:1,2,3')
    content = Column(Text, nullable=True, comment='客户描述')
    market = Column(Text, nullable=True, comment='主要经营业务')
    remark = Column(Text, nullable=True, comment='备注信息')
    tax_bank = Column(String(100), nullable=False, server_default="''", comment='开户银行')
    tax_banksn = Column(String(100), nullable=False, server_default="''", comment='银行帐号')
    tax_num = Column(String(100), nullable=False, server_default="''", comment='纳税人识别号')
    tax_mobile = Column(String(20), nullable=False, server_default="''", comment='开票电话')
    tax_address = Column(String(200), nullable=False, server_default="''", comment='开票地址')
    is_lock = Column(Integer, nullable=False, server_default='0', comment='锁定状态：0 未锁，1 已锁')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='添加时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='修改时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')
