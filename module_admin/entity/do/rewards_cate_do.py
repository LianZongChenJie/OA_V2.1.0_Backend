from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from config.database import Base
from config.env import DataBaseConfig
from utils.common_util import SqlalchemyUtil


class SysRewardsCate(Base):
    """
    奖罚项目表
    """

    __tablename__ = 'oa_rewards_cate'
    __table_args__ = {'comment': '奖罚项目'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='奖罚项目 ID')
    title = Column(String(100), nullable=False, server_default="''", comment='奖罚项目名称')
    status = Column(Integer, nullable=True, server_default='1', comment='状态：-1删除 0禁用 1启用')
    create_time = Column(BigInteger, nullable=True, server_default='0', comment='创建时间')
    update_time = Column(BigInteger, nullable=True, server_default='0', comment='更新时间')
