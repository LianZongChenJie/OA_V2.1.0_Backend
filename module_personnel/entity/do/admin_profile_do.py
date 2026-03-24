from config.database import Base
from sqlalchemy import Column, Integer, String, SmallInteger, Text, BigInteger
class OaAdminProfiles(Base):
    """员工档案实体类"""

    __tablename__ = 'oa_admin_profiles'
    __table_args__ = {'comment': '员工档案表'}

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 关联信息
    admin_id = Column(Integer, nullable=False, default=0, comment='员工ID')

    # 类型
    types = Column(SmallInteger, nullable=False, default=0,
                   comment='类型:1教育经历/2工作经历/3相关证书/4计算机技能/5语言能力')

    # 基本信息
    title = Column(String(255), nullable=False, default='', comment='院校/培训机构/公司名称/证书名称/技能名称/语言名称')
    start_time = Column(String(255), nullable=False, default='', comment='开始时间')
    end_time = Column(String(255), nullable=False, default='', comment='结束时间')

    # 教育相关字段
    speciality = Column(String(50), nullable=False, default='', comment='所学专业')
    education = Column(String(50), nullable=False, default='', comment='所获学历')
    authority = Column(String(50), nullable=False, default='', comment='颁发机构')

    # 工作相关字段
    position = Column(String(50), nullable=False, default='', comment='职位')

    # 技能相关字段
    know = Column(Integer, nullable=False, default=0, comment='熟悉程度')

    # 备注
    remark = Column(Text, nullable=True, comment='备注说明')

    # 排序
    sort = Column(Integer, nullable=False, default=0, comment='排序')

    # 时间戳
    create_time = Column(BigInteger, nullable=False, default=0, comment='添加时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='修改时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    