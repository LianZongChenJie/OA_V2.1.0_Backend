from sqlalchemy import Column
from sqlalchemy import Integer, String, BigInteger, SmallInteger, Text
from config.database import Base
from typing import Optional


class OaTalent(Base):
    """入职申请表实体类"""

    __tablename__ = 'oa_talent'
    __table_args__ = (
        {'comment': '入职申请表'}
    )

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='ID')

    # 基本信息
    name = Column(String(255), nullable=False, default='', comment='姓名')
    email = Column(String(255), nullable=False, default='', comment='电子邮箱')
    mobile = Column(BigInteger, nullable=False, default=0, comment='手机号码')
    sex = Column(Integer, nullable=False, default=0, comment='性别:1男,2女')

    # 部门信息
    to_did = Column(Integer, nullable=False, default=0, comment='所属部门')
    to_dids = Column(String(500), nullable=False, default='', comment='次部门')

    # 头像
    thumb = Column(String(255), nullable=False, comment='头像')

    # 职位信息
    position_id = Column(Integer, nullable=False, default=0, comment='职位id')
    type = Column(Integer, nullable=False, default=0, comment='员工类型:0未设置,1正式,2试用,3实习')
    position_name = Column(Integer, nullable=False, default=0, comment='应聘职务')
    position_rank = Column(Integer, nullable=False, default=0, comment='应聘职级')

    # 工号
    job_number = Column(String(255), nullable=False, default='', comment='工号')

    # 个人信息
    birthday = Column(String(255), nullable=False, default='', comment='生日')
    pid = Column(Integer, nullable=False, default=0, comment='上级领导')
    work_date = Column(String(255), nullable=False, default='', comment='开始工作时间')
    work_location = Column(Integer, nullable=False, default=0, comment='工作地点')
    native_place = Column(String(255), nullable=False, default='', comment='籍贯')
    nation = Column(String(255), nullable=False, default='', comment='民族')
    home_address = Column(String(255), nullable=False, default='', comment='家庭地址')
    current_address = Column(String(255), nullable=False, default='', comment='现居地址')
    contact = Column(String(255), nullable=False, default='', comment='紧急联系人')
    contact_mobile = Column(String(255), nullable=False, default='', comment='紧急联系人电话')

    # 户口信息
    resident_type = Column(Integer, nullable=False, default=0, comment='户口性质:1农村户口,2城镇户口')
    resident_place = Column(String(255), nullable=False, default='', comment='户口所在地')

    # 教育信息
    graduate_school = Column(String(255), nullable=False, default='', comment='毕业学校')
    graduate_day = Column(String(255), nullable=False, default='毕业日期', comment='毕业日期')
    political = Column(Integer, nullable=False, default=1, comment='政治面貌:1中共党员,2团员')
    marital_status = Column(Integer, nullable=False, default=1, comment='婚姻状况:1未婚,2已婚,3离异')
    idcard = Column(String(255), nullable=False, default='', comment='身份证')
    education = Column(String(255), nullable=False, default='', comment='学位')
    speciality = Column(String(255), nullable=False, default='', comment='专业')

    # 薪资信息
    bank_account = Column(String(255), nullable=False, default='', comment='银行卡号')
    social_account = Column(String(255), nullable=False, default='', comment='社保账号')
    salary = Column(Integer, nullable=False, default=0, comment='期望薪资')
    salary_remark = Column(String(255), nullable=False, default='', comment='薪资备注')

    # 推荐人信息
    reference_name = Column(String(255), nullable=False, default='', comment='推荐人姓名')
    reference_rel = Column(String(255), nullable=False, default='', comment='推荐人关系')
    reference_mobile = Column(String(255), nullable=False, default='', comment='推荐人联系方式')

    # 附件和描述
    file_ids = Column(String(500), nullable=False, default='', comment='档案附件')
    desc = Column(Text, comment='个人简介')
    remark = Column(String(1000), default='', comment='入职评语')

    # 入职信息
    entry_time = Column(BigInteger, nullable=False, default=0, comment='入职时间')
    is_staff = Column(Integer, nullable=False, default=1, comment='身份类型:1普通员工,2劳务派遣')
    status = Column(Integer, nullable=False, default=1, comment='状态:1正常,2已入职')

    # 创建信息
    admin_id = Column(Integer, nullable=False, default=0, comment='创建人')
    did = Column(Integer, nullable=False, default=0, comment='创建部门')
    create_time = Column(BigInteger, nullable=False, default=0, comment='申请时间')

    # 审核信息
    check_status = Column(SmallInteger, nullable=False, default=0,
                          comment='审核状态:0待审核,1审核中,2审核通过,3审核不通过,4撤销审核')
    check_flow_id = Column(Integer, nullable=False, default=0, comment='审核流程id')
    check_step_sort = Column(Integer, nullable=False, default=0, comment='当前审批步骤')
    check_uids = Column(String(500), nullable=False, default='', comment='当前审批人ID，如:1,2,3')
    check_last_uid = Column(String(500), nullable=False, default='', comment='上一审批人')
    check_history_uids = Column(String(500), nullable=False, default='', comment='历史审批人ID，如:1,2,3')
    check_copy_uids = Column(String(500), nullable=False, default='', comment='抄送人ID，如:1,2,3')
    check_time = Column(BigInteger, nullable=False, default=0, comment='审核通过时间')

    # 时间戳
    update_time = Column(BigInteger, nullable=False, default=0, comment='更新信息时间')
    delete_time = Column(BigInteger, nullable=False, default=0, comment='删除时间')
    talent_id = Column(Integer, nullable=False, default=0, comment='入职申请id')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}