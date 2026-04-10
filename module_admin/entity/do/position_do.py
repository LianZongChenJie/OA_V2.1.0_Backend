from sqlalchemy import BigInteger, Column, Integer, SmallInteger, String

from config.database import Base


class OaPosition(Base):
    """
    岗位职称表
    """

    __tablename__ = 'oa_position'
    __table_args__ = {'comment': '岗位职称'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='ID')
    title = Column(String(100), nullable=False, server_default='', comment='岗位名称')
    work_price = Column(Integer, nullable=False, server_default='0', comment='工时单价')
    remark = Column(String(1000), nullable=True, server_default='', comment='备注')
    status = Column(SmallInteger, nullable=False, server_default='1', comment='状态：-1删除 0禁用 1启用')
    create_time = Column(BigInteger, nullable=False, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=False, server_default='0', comment='更新时间')
