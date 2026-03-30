from sqlalchemy import BigInteger, Column, Integer, String, Text

from config.database import Base


class OaCustomerContact(Base):
    """
    客户联系人表
    """

    __tablename__ = 'oa_customer_contact'
    __table_args__ = {'comment': '客户联系人表'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='联系人 ID')
    cid = Column(Integer, nullable=False, server_default='0', comment='客户 ID')
    is_default = Column(Integer, nullable=False, server_default='0', comment='是否是第一联系人')
    name = Column(String(100), nullable=False, server_default="''", comment='姓名')
    sex = Column(Integer, nullable=False, server_default='0', comment='用户性别:0 未知，1 男，2 女')
    mobile = Column(String(20), nullable=False, server_default="''", comment='手机号码')
    qq = Column(String(20), nullable=False, server_default="''", comment='QQ 号')
    wechat = Column(String(20), nullable=False, server_default="''", comment='微信号')
    email = Column(String(100), nullable=False, server_default="''", comment='邮件地址')
    nickname = Column(String(50), nullable=False, server_default="''", comment='称谓')
    department = Column(String(50), nullable=False, server_default="''", comment='部门')
    position = Column(String(50), nullable=False, server_default="''", comment='职位')
    birthday = Column(String(50), nullable=False, server_default="''", comment='生日')
    address = Column(String(255), nullable=False, server_default="''", comment='家庭住址')
    family = Column(Text, nullable=True, comment='家庭成员')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='创建人')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')

