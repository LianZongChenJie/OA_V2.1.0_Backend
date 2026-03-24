from sqlalchemy import Column, Integer, String, BigInteger, Numeric, SmallInteger, Text
from config.database import Base

class OaCar(Base):
    """
    车辆管理表
    """
    __tablename__ = 'oa_car'
    __table_args__ = {'comment': '车辆管理'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    title = Column(String(100), nullable=False, server_default="''", comment='车辆名称')
    name = Column(String(100), nullable=False, server_default="''", comment='车辆牌号')
    oil = Column(String(100), nullable=False, server_default="''", comment='油耗')
    mileage = Column(Numeric(15, 2), nullable=False, server_default='0.00', comment='开始里程数')
    seats = Column(Integer, nullable=False, server_default='5', comment='座位数')
    color = Column(String(100), nullable=False, server_default="''", comment='车身颜色')
    vin = Column(String(100), nullable=False, server_default="''", comment='车架号')
    engine = Column(String(100), nullable=False, server_default="''", comment='发动机号')
    buy_time = Column(BigInteger, nullable=False, server_default='0', comment='购买日期时间戳')
    price = Column(Numeric(15, 2), nullable=False, server_default='0.00', comment='购买价格')
    thumb = Column(Integer, nullable=False, server_default='5', comment='车辆照片 ID')
    types = Column(SmallInteger, nullable=False, server_default='5', comment='车辆类型:1 轿车，2 面包车，3 越野车，4 吉普车，5 巴士，6 工具车，7 卡车，8 其他')
    driver = Column(Integer, nullable=False, server_default='0', comment='驾驶员 ID')
    insure_time = Column(BigInteger, nullable=False, server_default='0', comment='保险到期时间时间戳')
    review_time = Column(BigInteger, nullable=False, server_default='0', comment='年审到期时间时间戳')
    file_ids = Column(String(500), nullable=False, server_default="''", comment='附件 ID，如:1,2,3')
    remark = Column(String(1000), nullable=False, server_default="''", comment='备注')
    status = Column(SmallInteger, nullable=False, server_default='1', comment='当前状态:1 可用，2 停用，3 维修，4 报废')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')


class OaCarRepair(Base):
    """
    车辆维修/保养记录表
    """
    __tablename__ = 'oa_car_repair'
    __table_args__ = {'comment': '车辆维修/保养记录表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    car_id = Column(Integer, nullable=False, server_default='0', comment='车辆 ID')
    repair_time = Column(BigInteger, nullable=False, server_default='0', comment='维修/保养时间时间戳')
    types = Column(SmallInteger, nullable=False, server_default='1', comment='类型:1 维修，2 保养')
    amount = Column(Numeric(15, 2), nullable=False, server_default='0.00', comment='维修/保养金额')
    content = Column(Text, nullable=True, comment='维修/保养原因')
    address = Column(String(255), nullable=False, server_default="''", comment='维修 (保养) 地点')
    file_ids = Column(String(500), nullable=False, server_default="''", comment='附件 ID，如:1,2,3')
    handled = Column(Integer, nullable=False, server_default='0', comment='经手人 ID')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='创建人')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')


class OaCarFee(Base):
    """
    车辆费用记录表
    """
    __tablename__ = 'oa_car_fee'
    __table_args__ = {'comment': '车辆费用记录表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    car_id = Column(Integer, nullable=False, server_default='0', comment='车辆 ID')
    title = Column(String(100), nullable=False, server_default="''", comment='费用主题')
    fee_time = Column(BigInteger, nullable=False, server_default='0', comment='费用时间时间戳')
    types = Column(SmallInteger, nullable=False, server_default='1', comment='费用类型 id')
    amount = Column(Numeric(15, 2), nullable=False, server_default='0.00', comment='金额')
    file_ids = Column(String(500), nullable=False, server_default="''", comment='附件 ID，如:1,2,3')
    content = Column(String(1000), nullable=True, comment='费用内容')
    handled = Column(Integer, nullable=False, server_default='0', comment='经手人 ID')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='创建人')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')


class OaCarMileage(Base):
    """
    车辆里程记录表
    """
    __tablename__ = 'oa_car_mileage'
    __table_args__ = {'comment': '车辆里程记录表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    car_id = Column(Integer, nullable=False, server_default='0', comment='车辆 ID')
    mileage = Column(Numeric(15, 2), nullable=False, server_default='0.00', comment='里程数')
    mileage_time = Column(BigInteger, nullable=False, server_default='0', comment='里程时间时间戳')
    admin_id = Column(Integer, nullable=False, server_default='0', comment='记录人 ID')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
    delete_time = Column(BigInteger, nullable=False, server_default='0', comment='删除时间')
