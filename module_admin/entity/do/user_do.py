from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String, Integer, Text

from config.database import Base
from config.env import DataBaseConfig
from utils.common_util import SqlalchemyUtil


class SysUser(Base):
    """
    用户信息表
    """

    __tablename__ = 'sys_user'
    __table_args__ = {'comment': '用户信息表'}

    user_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='用户ID')
    dept_id = Column(
        BigInteger,
        nullable=True,
        server_default=SqlalchemyUtil.get_server_default_null(DataBaseConfig.db_type, False),
        comment='部门ID',
    )
    did = Column(Integer, nullable=False, comment='岗位ID')
    pid = Column(Integer, nullable=False, comment='部门ID')
    position_id = Column(Integer, nullable=False, comment='职位ID')
    position_name = Column(Integer, nullable=False, comment='职务')
    position_rank = Column(Integer, nullable=False, comment='职务等级')
    user_name = Column(String(30), nullable=False, comment='用户账号')
    nick_name = Column(String(30), nullable=False, comment='用户昵称')
    user_type = Column(String(2), nullable=True, server_default='00', comment='用户类型（00系统用户，0未设置,1正式,2试用,3实习）')
    is_staff = Column(CHAR(1), nullable=True, server_default='0', comment='身份类型:1企业员工,2劳务派遣,3兼职员工）')
    email = Column(String(50), nullable=True, server_default="''", comment='用户邮箱')
    phonenumber = Column(String(11), nullable=True, server_default="''", comment='手机号码')
    job_number = Column(String(255), nullable=True, server_default="''", comment='员工编号')
    birthday = Column(String(255), nullable=True, server_default="''", comment='出生日期')
    age = Column(Integer, nullable=True, server_default="''", comment='年龄')
    work_date = Column(String(255), nullable=True, server_default="''", comment='开始办公日期')
    work_location = Column(Integer, nullable=True, server_default="''", comment='办公地点')
    native_place = Column(String(255), nullable=True, server_default="''", comment='籍贯')
    nation = Column(String(255), nullable=True, server_default="''", comment='民族')
    home_address = Column(String(255), nullable=True, server_default="''", comment='家庭地址')
    current_address = Column(String(255), nullable=True, server_default="''", comment='现居住地')
    contact = Column(String(255), nullable=True, server_default="''", comment='紧急联系人')
    contact_mobile = Column(String(255), nullable=True, server_default="''", comment='紧急联系方式')
    resident_type = Column(Integer, nullable=True, server_default="''", comment='户籍类型：1城镇，2农村')
    resident_place = Column(String(255), nullable=True, server_default="''", comment='户籍地址')
    graduate_school = Column(String(255), nullable=True, server_default="''", comment='毕业院校')
    graduate_day = Column(String(255), nullable=True, server_default="''", comment='毕业日期')
    political = Column(String(255), nullable=True, server_default="''", comment='政治面貌')
    marital_status = Column(Integer, nullable=True, server_default="''", comment='婚姻状况：1已婚，2未婚,3离异')
    idcard = Column(String(255), nullable=True, server_default="''", comment='身份证号')
    education = Column(String(255), nullable=True, server_default="''", comment='学位')
    speciality = Column(String(255), nullable=True, server_default="''", comment='专业')
    social_account = Column(String(255), nullable=True, server_default="''", comment='社保账号')
    medical_account = Column(String(255), nullable=True, server_default="''", comment='医保账号')
    provident_account = Column(String(255), nullable=True, server_default="''", comment='公积金账号')
    bank_account = Column(String(255), nullable=True, server_default="''", comment='银行账号')
    bank_info = Column(String(255), nullable=True, server_default="''", comment='开户行')
    sex = Column(CHAR(1), nullable=True, server_default='0', comment='用户性别（0男 1女 2未知）')
    avatar = Column(String(100), nullable=True, server_default="''", comment='头像地址')
    file_ids = Column(String(500), nullable=True, server_default="''", comment='档案ID')
    user_desc = Column(Text, nullable=True, server_default="''", comment='员工简介')
    is_hide = Column(CHAR(1), nullable=True, server_default='0', comment='是否隐藏联系信息（0显示 1隐藏）')
    entry_time = Column(String(255), nullable=True, server_default="''", comment='入职日期')
    delete_date = Column(String(255), nullable=True, server_default="''", comment='删除时间')
    password = Column(String(100), nullable=True, server_default="''", comment='密码')
    status = Column(CHAR(1), nullable=True, server_default='0', comment='帐号状态（0正常 1停用）')
    del_flag = Column(CHAR(1), nullable=True, server_default='0', comment='删除标志（0代表存在 2代表删除）')
    login_ip = Column(String(128), nullable=True, server_default="''", comment='最后登录IP')
    login_num = Column(Integer, nullable=True, server_default="''", comment='登录次数')
    login_date = Column(DateTime, nullable=True, comment='最后登录时间')
    is_lock = Column(CHAR(1), nullable=True, server_default='0', comment='是否锁屏')
    pwd_update_date = Column(DateTime, nullable=True, comment='密码最后更新时间')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, comment='创建时间', default=datetime.now())
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, comment='更新时间', default=datetime.now())
    remark = Column(
        String(500),
        nullable=True,
        server_default=SqlalchemyUtil.get_server_default_null(DataBaseConfig.db_type),
        comment='备注',
    )
    auth_did = Column(Integer, nullable=True, server_default="''", comment='数据权限类型:0仅自己关联的数据,1所属主部门的数据,2所属次部门的数据,3所属主次部门的数据,4所属主部门及其子部门数据,5所属次部门及其子部门数据,6所属主次部门及其子部门数据,7所属主部门所在顶级部门及其子部门数据,8所属次部门所在顶级部门及其子部门数据,9所属主次部门所在顶级部门及其子部门数据,10所有部门数据')
    auth_dids = Column(String(500), nullable=True, server_default="''", comment='可见部门数据')
    son_dids = Column(String(500), nullable=True, server_default="''", comment='可见子部门数据')
    admin_status = Column(Integer, nullable=True, server_default="''", comment='员工状态：-1待入职,0禁止登录,1正常,2离职')


class SysUserRole(Base):
    """
    用户和角色关联表
    """

    __tablename__ = 'sys_user_role'
    __table_args__ = {'comment': '用户和角色关联表'}

    user_id = Column(BigInteger, primary_key=True, nullable=False, comment='用户ID')
    role_id = Column(BigInteger, primary_key=True, nullable=False, comment='角色ID')


class SysUserPost(Base):
    """
    用户与岗位关联表
    """

    __tablename__ = 'sys_user_post'
    __table_args__ = {'comment': '用户与岗位关联表'}

    user_id = Column(BigInteger, primary_key=True, nullable=False, comment='用户ID')
    post_id = Column(BigInteger, primary_key=True, nullable=False, comment='岗位ID')
