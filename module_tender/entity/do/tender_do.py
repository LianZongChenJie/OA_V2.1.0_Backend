"""
招标文件智能生成模块 DO 实体类
"""
from config.database import Base
from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, Text, Numeric


class OaTenderDocument(Base):
    """招标文件信息表实体类"""

    __tablename__ = 'oa_tender_document'
    __table_args__ = {'comment': '招标文件信息表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    tender_uuid = Column(String(64), nullable=False, unique=True, comment='招标文件UUID')
    file_name = Column(String(256), nullable=False, default='', comment='原始文件名')
    tender_name = Column(String(256), nullable=False, default='', comment='招标项目名称')
    tender_code = Column(String(128), nullable=False, default='', comment='招标编号')
    company_name = Column(String(256), nullable=False, default='', comment='招标单位')
    total_pages = Column(Integer, nullable=False, default=0, comment='总页数')
    status = Column(SmallInteger, nullable=False, default=0, comment='状态:0已解析,1匹配中,2已完成')
    requirements_json = Column(Text, nullable=False, default='', comment='人员配置要求JSON')
    score_standard_json = Column(Text, nullable=False, default='', comment='评标标准JSON')
    file_path = Column(String(500), nullable=False, default='', comment='原始文件路径')
    generated_file_path = Column(String(500), nullable=False, default='', comment='生成的投标文件路径')
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新时间')

    def __repr__(self) -> str:
        return f"<OaTenderDocument(id={self.id}, tender_name='{self.tender_name}', tender_code='{self.tender_code}')>"


class OaTenderRequirement(Base):
    """招标要求明细表实体类"""

    __tablename__ = 'oa_tender_requirement'
    __table_args__ = {'comment': '招标要求明细表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    tender_id = Column(Integer, nullable=False, default=0, comment='关联招标文件ID')
    requirement_type = Column(String(64), nullable=False, default='', comment='要求类型:学历/工作/技能/证书/业绩')
    requirement_key = Column(String(128), nullable=False, default='', comment='要求键:education/work_years/skills/certificates')
    operator = Column(String(32), nullable=False, default='', comment='运算符:eq/gte/lte/contains/in')
    requirement_value = Column(String(500), nullable=False, default='', comment='要求值')
    score_weight = Column(Numeric(5, 2), nullable=False, default=0, comment='评分权重(0-100)')
    description = Column(Text, nullable=False, default='', comment='要求描述')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')

    def __repr__(self) -> str:
        return f"<OaTenderRequirement(id={self.id}, tender_id={self.tender_id}, type='{self.requirement_type}')>"


class OaBidPersonnelMapping(Base):
    """投标人员映射表实体类"""

    __tablename__ = 'oa_bid_personnel_mapping'
    __table_args__ = {'comment': '投标人员映射表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')
    tender_id = Column(Integer, nullable=False, default=0, comment='关联招标文件ID')
    resume_id = Column(Integer, nullable=False, default=0, comment='简历ID')
    match_score = Column(Numeric(5, 2), nullable=False, default=0, comment='匹配得分')
    match_reason = Column(Text, nullable=False, default='', comment='匹配原因')
    sort_order = Column(Integer, nullable=False, default=0, comment='排序序号')
    is_selected = Column(SmallInteger, nullable=False, default=0, comment='是否选中:1选中,0推荐中')
    create_time = Column(BigInteger, nullable=False, default=0, comment='创建时间')

    def __repr__(self) -> str:
        return f"<OaBidPersonnelMapping(id={self.id}, tender_id={self.tender_id}, resume_id={self.resume_id}, score={self.match_score})>"
