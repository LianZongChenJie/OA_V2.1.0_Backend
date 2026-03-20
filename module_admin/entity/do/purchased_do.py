from config.database import Base
from sqlalchemy import Column, Integer, String, Numeric, Text, BigInteger, SmallInteger


class OaPurchased(Base):
    """采购品表实体类"""

    __tablename__ = 'oa_purchased'
    __table_args__ = {'comment': '采购品表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    title = Column(String(100), nullable=False, default='', comment='采购品名称')
    cate_id = Column(Integer, nullable=False, default=0, comment='采购分类 id')
    thumb = Column(Integer, nullable=False, default=0, comment='缩略图 id')
    code = Column(String(255), nullable=False, default='', comment='产品编码')
    barcode = Column(String(255), nullable=False, default='', comment='条形码')
    unit = Column(String(100), nullable=False, default='', comment='单位')
    specs = Column(String(100), nullable=False, default='', comment='规格')
    brand = Column(String(100), nullable=False, default='', comment='品牌')
    producer = Column(String(100), nullable=False, default='', comment='生产商')

    # 价格信息
    purchase_price = Column(Numeric(15, 2), nullable=False, default=0.00, comment='采购价')
    sale_price = Column(Numeric(15, 2), nullable=False, default=0.00, comment='销售价')

    # 描述和附件
    content = Column(Text, comment='商品描述')
    album_ids = Column(String(255), nullable=False, default='', comment='采购品相册 ids')
    file_ids = Column(String(255), nullable=False, default='', comment='采购品附件 ids')

    # 库存和类型
    stock = Column(Integer, nullable=False, default=0, comment='库存')
    is_object = Column(SmallInteger, nullable=False, default=1, comment='是否是实物，1 是 2 不是')

    # 状态
    status = Column(SmallInteger, nullable=False, default=1, comment='状态：0 禁用 1 启用')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def __repr__(self) -> str:
        return f"<OaPurchased(id={self.id}, title='{self.title}', code='{self.code}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'cate_id': self.cate_id,
            'thumb': self.thumb,
            'code': self.code,
            'barcode': self.barcode,
            'unit': self.unit,
            'specs': self.specs,
            'brand': self.brand,
            'producer': self.producer,
            'purchase_price': float(self.purchase_price) if self.purchase_price else 0.00,
            'sale_price': float(self.sale_price) if self.sale_price else 0.00,
            'content': self.content,
            'album_ids': self.album_ids,
            'file_ids': self.file_ids,
            'stock': self.stock,
            'is_object': self.is_object,
            'status': self.status,
            'create_time': self.create_time,
            'update_time': self.update_time,
            'delete_time': self.delete_time
        }
