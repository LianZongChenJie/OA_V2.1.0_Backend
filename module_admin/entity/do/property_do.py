from sqlalchemy import Column, Integer, String, BigInteger, Text, SmallInteger, Numeric
from config.database import Base

class OaProperty(Base):
    """
    资产表
    """
    __tablename__ = 'oa_property'
    __table_args__ = {'comment': '资产表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    title = Column(String(100), nullable=False, server_default="''", comment='名称')
    code = Column(String(100), nullable=False, server_default="''", comment='编号')
    thumb = Column(Integer, nullable=False, server_default='0', comment='缩略图ID')
    cate_id = Column(Integer, nullable=False, server_default='0', comment='资产分类id')
    brand_id = Column(Integer, nullable=False, server_default='0', comment='品牌名称id')
    unit_id = Column(Integer, nullable=False, server_default='0', comment='单位id')
    quality_time = Column(BigInteger, nullable=False, server_default='0', comment='质保到期日期时间戳')
    buy_time = Column(BigInteger, nullable=False, server_default='0', comment='购进日期时间戳')

    # 【修正点 1】使用 sqlalchemy.Numeric 替代 python decimal.Decimal
    # 格式：Numeric(precision, scale) -> Numeric(15, 2)
    price = Column(Numeric(15, 2), nullable=False, server_default='0.00', comment='价格')
    rate = Column(Numeric(15, 2), nullable=False, server_default='0.00', comment='年折旧率')

    model = Column(String(255), nullable=False, server_default="''", comment='规格型号')
    address = Column(String(255), nullable=False, server_default="''", comment='所放位置')
    user_dids = Column(String(255), nullable=False, server_default="''", comment='使用部门ids')
    user_ids = Column(String(255), nullable=False, server_default="''", comment='使用人员ids')
    content = Column(Text, nullable=True, comment='资产描述')
    file_ids = Column(String(255), nullable=False, server_default="''", comment='资产附件ids')

    # 【修正点 2】SmallInteger 是合法的，但为了保持与你之前正常文件风格一致，也可以用 Integer
    # 这里保留 SmallInteger，因为它在 SQLAlchemy 中是有效的
    source = Column(SmallInteger, nullable=False, server_default='1', comment='来源：1采购,2赠与,3自产,4其他')
    purchase_id = Column(Integer, nullable=False, server_default='0', comment='采购单ID')
    status = Column(SmallInteger, nullable=False, server_default='1', comment='状态：-1删除 0闲置,1在用,2维修,3报废,4丢失')

    admin_id = Column(Integer, nullable=False, server_default='0', comment='创建人')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_id = Column(Integer, nullable=False, server_default='0', comment='编辑人')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')