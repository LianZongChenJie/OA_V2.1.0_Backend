import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import Network, NotBlank, Size, Xss

from exceptions.exception import ModelValidatorException
from module_admin.entity.vo.dept_vo import DeptModel
from module_admin.entity.vo.post_vo import PostModel
from module_admin.entity.vo.role_vo import RoleModel


class TokenData(BaseModel):
    """
    token解析结果
    """

    user_id: int | None = Field(default=None, description='用户ID')


class UserModel(BaseModel):
    """
    用户表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    user_id: int | None = Field(default=None, description='用户ID')
    dept_id: int | None = Field(default=None, description='部门ID')
    did: int | None = Field(default=None, description='岗位ID')
    pid: int | None = Field(default=None, description='部门ID')
    position_id: int | None = Field(default=None, description='职位ID')
    position_name: int | None = Field(default=None, description='职务')
    position_rank: int | None = Field(default=None, description='职务等级')
    user_name: str | None = Field(default=None, description='用户账号')
    nick_name: str | None = Field(default=None, description='用户昵称')
    user_type: str | None = Field(default=None, description='用户类型（00系统用户）')
    is_staff: int | None = Field(default=None, description='身份类型:1企业员工,2劳务派遣,3兼职员工）')
    email: str | None = Field(default=None, description='用户邮箱')
    phonenumber: str | None = Field(default=None, description='手机号码')
    job_number: str | None = Field(default=None, description='员工编号')
    birthday: str | None = Field(default=None, description='出生日期')
    age: int | None = Field(default=None, description='年龄')
    work_date: str | None = Field(default=None, description='开始办公日期')
    work_location: int | None = Field(default=None, description='办公地点')
    native_place: str | None = Field(default=None, description='籍贯')
    nation: str | None = Field(default=None, description='民族')
    home_address: str | None = Field(default=None, description='家庭地址')
    current_address: str | None = Field(default=None, description='现居住地')
    contact: str | None = Field(default=None, description='紧急联系人')
    contact_mobile: str | None = Field(default=None, description='紧急联系方式')
    resident_type: int | None = Field(default=None, description='户籍类型：1城镇，2农村')
    resident_place: str | None = Field(default=None, description='户籍地址')
    graduate_school: str | None = Field(default=None, description='毕业院校')
    graduate_day: str | None = Field(default=None, description='毕业日期')
    political: int | None = Field(default=None, description='政治面貌')
    marital_status: int | None = Field(default=None, description='婚姻状况：1已婚，2未婚,3离异')
    idcard: str | None = Field(default=None, description='身份证号')
    education: str | None = Field(default=None, description='文化程度')
    speciality: str | None = Field(default=None, description='专业')
    social_account: str | None = Field(default=None, description='社保账号')
    medical_account: str | None = Field(default=None, description='医保账号')
    provident_account: str | None = Field(default=None, description='公积金账号')
    bank_account: str | None = Field(default=None, description='银行账号')
    bank_info: str | None = Field(default=None, description='开户行')
    sex: Literal['0', '1', '2'] | None = Field(default=None, description='用户性别（0男 1女 2未知）')
    avatar: str | None = Field(default=None, description='头像地址')
    file_ids: str | None = Field(default=None, description='档案ID')
    user_desc: str | None = Field(default=None, description='员工简介')
    is_hide: int | None = Field(default=None, description='是否隐藏联系方式')
    entry_date: str | None = Field(default=None, description='入职日期')
    delete_time: int | None = Field(default=None, description='删除时间')
    password: str | None = Field(default=None, description='密码')
    status: Literal['0', '1'] | None = Field(default=None, description='帐号状态（0正常 1停用）')
    del_flag: Literal['0', '2'] | None = Field(default=None, description='删除标志（0代表存在 2代表删除）')
    login_ip: str | None = Field(default=None, description='最后登录IP')
    login_date: datetime | None = Field(default=None, description='最后登录时间')
    is_lock: int | None = Field(default=None, description='是否锁屏')
    pwd_update_date: datetime | None = Field(default=None, description='密码最后更新时间')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')
    remark: str | None = Field(default=None, description='备注')
    admin: bool | None = Field(default=False, description='是否为admin')
    auth_did: int | None = Field(default=None, description='数据权限类型:0仅自己关联的数据,1所属主部门的数据,2所属次部门的数据,3所属主次部门的数据,4所属主部门及其子部门数据,5所属次部门及其子部门数据,6所属主次部门及其子部门数据,7所属主部门所在顶级部门及其子部门数据,8所属次部门所在顶级部门及其子部门数据,9所属主次部门所在顶级部门及其子部门数据,10所有部门数据')
    auth_dids: str | None = Field(default=None, description='可见部门数据')
    son_dids: str | None = Field(default=None, description='可见子部门数据')
    admin_status: int | None = Field(default=None, description='员工状态：-1待入职,0禁止登录,1正常,2离职')
    @model_validator(mode='after')
    def check_password(self) -> 'UserModel':
        pattern = r"""^[^<>"'|\\]+$"""
        if self.password is None or re.match(pattern, self.password):
            return self
        raise ModelValidatorException(message='密码不能包含非法字符：< > " \' \\ |')

    @model_validator(mode='after')
    def check_admin(self) -> 'UserModel':
        if self.user_id == 1:
            self.admin = True
        else:
            self.admin = False
        return self

    @Xss(field_name='user_name', message='用户账号不能包含脚本字符')
    @NotBlank(field_name='user_name', message='用户账号不能为空')
    @Size(field_name='user_name', min_length=0, max_length=30, message='用户账号长度不能超过30个字符')
    def get_user_name(self) -> str | None:
        return self.user_name

    @Xss(field_name='nick_name', message='用户昵称不能包含脚本字符')
    @Size(field_name='nick_name', min_length=0, max_length=30, message='用户昵称长度不能超过30个字符')
    def get_nick_name(self) -> str | None:
        return self.nick_name

    @Network(field_name='email', field_type='EmailStr', message='邮箱格式不正确')
    @Size(field_name='email', min_length=0, max_length=50, message='邮箱长度不能超过50个字符')
    def get_email(self) -> str | None:
        return self.email

    @Size(field_name='phonenumber', min_length=0, max_length=11, message='手机号码长度不能超过11个字符')
    def get_phonenumber(self) -> str | None:
        return self.phonenumber

    def validate_fields(self) -> None:
        self.get_user_name()
        self.get_nick_name()
        self.get_email()
        self.get_phonenumber()


class UserRowModel(UserModel):
    """
    用户列表行数据模型
    """

    dept: DeptModel | None = Field(default=None, description='部门信息')


class UserRoleModel(BaseModel):
    """
    用户和角色关联表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    user_id: int | None = Field(default=None, description='用户ID')
    role_id: int | None = Field(default=None, description='角色ID')


class UserPostModel(BaseModel):
    """
    用户与岗位关联表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    user_id: int | None = Field(default=None, description='用户ID')
    post_id: int | None = Field(default=None, description='岗位ID')


class UserInfoModel(UserModel):
    post_ids: str | None | None = Field(default=None, description='岗位ID信息')
    role_ids: str | None | None = Field(default=None, description='角色ID信息')
    dept: DeptModel | None | None = Field(default=None, description='部门信息')
    role: list[RoleModel | None] | None = Field(default=[], description='角色信息')


class CurrentUserModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    permissions: list = Field(description='权限信息')
    roles: list = Field(description='角色信息')
    user: UserInfoModel | None = Field(description='用户信息')
    is_default_modify_pwd: bool = Field(default=False, description='是否初始密码修改提醒')
    is_password_expired: bool = Field(default=False, description='密码是否过期提醒')


class UserDetailModel(BaseModel):
    """
    获取用户详情信息响应模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    data: UserInfoModel | None | None = Field(default=None, description='用户信息')
    post_ids: list | None = Field(default=None, description='岗位ID信息')
    posts: list[PostModel | None] = Field(description='岗位信息')
    role_ids: list | None = Field(default=None, description='角色ID信息')
    roles: list[RoleModel | None] = Field(description='角色信息')


class UserProfileModel(BaseModel):
    """
    获取个人信息响应模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    data: UserInfoModel | None = Field(description='用户信息')
    post_group: str | None = Field(description='岗位信息')
    role_group: str | None = Field(description='角色信息')


class AvatarModel(BaseModel):
    """
    上传头像响应模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    img_url: str = Field(description='头像地址')


class UserQueryModel(UserModel):
    """
    用户管理不分页查询模型
    """

    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')


class UserPageQueryModel(UserQueryModel):
    """
    用户管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddUserModel(UserModel):
    """
    新增用户模型
    """

    role_ids: list | None = Field(default=[], description='角色ID信息')
    post_ids: list | None = Field(default=[], description='岗位ID信息')
    type: str | None = Field(default=None, description='操作类型')


class EditUserModel(AddUserModel):
    """
    编辑用户模型
    """

    role: list | None = Field(default=[], description='角色信息')


class ResetPasswordModel(BaseModel):
    """
    重置密码模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    old_password: str | None = Field(default=None, description='旧密码')
    new_password: str | None = Field(default=None, description='新密码')

    @model_validator(mode='after')
    def check_new_password(self) -> 'ResetPasswordModel':
        pattern = r"""^[^<>"'|\\]+$"""
        if self.new_password is None or re.match(pattern, self.new_password):
            return self
        raise ModelValidatorException(message='密码不能包含非法字符：< > " \' \\ |')


class ResetUserModel(UserModel):
    """
    重置用户密码模型
    """

    old_password: str | None = Field(default=None, description='旧密码')
    sms_code: str | None = Field(default=None, description='验证码')
    session_id: str | None = Field(default=None, description='会话id')


class DeleteUserModel(BaseModel):
    """
    删除用户模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    user_ids: str = Field(description='需要删除的用户ID')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')


class UserRoleQueryModel(UserModel):
    """
    用户角色关联管理不分页查询模型
    """

    role_id: int | None = Field(default=None, description='角色ID')


class UserRolePageQueryModel(UserRoleQueryModel):
    """
    用户角色关联管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class SelectedRoleModel(RoleModel):
    """
    是否选择角色模型
    """

    flag: bool | None = Field(default=False, description='选择标识')


class UserRoleResponseModel(BaseModel):
    """
    用户角色关联管理列表返回模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    roles: list[SelectedRoleModel | None] = Field(default=[], description='角色信息')
    user: UserInfoModel = Field(description='用户信息')


class CrudUserRoleModel(BaseModel):
    """
    新增、删除用户关联角色及角色关联用户模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    user_id: int | None = Field(default=None, description='用户ID')
    user_ids: str | None = Field(default=None, description='用户ID信息')
    role_id: int | None = Field(default=None, description='角色ID')
    role_ids: str | None = Field(default=None, description='角色ID信息')
