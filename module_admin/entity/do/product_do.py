from decimal import Decimal as PyDecimal

from sqlalchemy import BigInteger, Column, Integer, Numeric, String, Text

from config.database import Base


class OaProduct(Base):
    """
    产品表
    """

    __tablename__ = 'oa_product'
    __table_args__ = {'comment': '产品表'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='产品 ID')
    title = Column(String(100), nullable=False, server_default="''", comment='产品名称')
    cate_id = Column(Integer, nullable=False, server_default='0', comment='产品分类 ID')
    thumb = Column(Integer, nullable=False, server_default='0', comment='缩略图 ID')
    code = Column(String(255), nullable=False, server_default="''", comment='产品编码')
    barcode = Column(String(255), nullable=False, server_default="''", comment='条形码')
    unit = Column(String(100), nullable=False, server_default="''", comment='单位')
    specs = Column(String(100), nullable=False, server_default="''", comment='规格')
    brand = Column(String(100), nullable=False, server_default="''", comment='品牌')
    producer = Column(String(100), nullable=False, server_default="''", comment='生产商')
    base_price = Column(Numeric(15, 2), nullable=False, server_default='0.00', comment='成本价')
    purchase_price = Column(Numeric(15, 2), nullable=False, server_default='0.00', comment='采购价')
    sale_price = Column(Numeric(15, 2), nullable=False, server_default='0.00', comment='销售价')
    content = Column(Text, nullable=True, comment='产品描述')
    album_ids = Column(String(255), nullable=False, server_default="''", comment='产品相册 ids')
    file_ids = Column(String(255), nullable=False, server_default="''", comment='产品附件 ids')
    stock = Column(Integer, nullable=False, server_default='0', comment='库存')
    is_object = Column(Integer, nullable=False, server_default='1', comment='是否是实物，1 是 2 不是')
    status = Column(Integer, nullable=False, server_default='1', comment='状态：0 禁用 1 启用')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='创建人')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')

