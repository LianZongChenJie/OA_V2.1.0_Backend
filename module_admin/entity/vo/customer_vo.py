from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class CustomerContactInfoModel(BaseModel):
    """
    客户联系人信息模型（用于新增客户时传入）
    """
    
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    
    name: str | None = Field(default=None, description='姓名')
    sex: int = Field(default=0, description='用户性别:0未知,1男,2女')
    mobile: str | None = Field(default=None, description='手机号码')
    qq: str | None = Field(default=None, description='QQ号')
    wechat: str | None = Field(default=None, description='微信号')
    email: str | None = Field(default=None, description='邮件地址')
    nickname: str | None = Field(default=None, description='称谓')
    department: str | None = Field(default=None, description='部门')
    position: str | None = Field(default=None, description='职位')
    birthday: str | None = Field(default=None, description='生日')
    address: str | None = Field(default=None, description='家庭住址')


class CustomerModel(BaseModel):
    """
    客户表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='客户 ID')
    name: str | None = Field(default=None, description='客户名称')
    source_id: int | None = Field(default=None, description='客户来源 id')
    grade_id: int | None = Field(default=None, description='客户等级 id')
    industry_id: int | None = Field(default=None, description='所属行业 id')
    services_id: int | None = Field(default=None, description='客户意向 id')
    provinceid: int | None = Field(default=None, description='省份 id')
    cityid: int | None = Field(default=None, description='城市 id')
    distid: int | None = Field(default=None, description='区县 id')
    townid: int | None = Field(default=None, description='城镇 id')
    address: str | None = Field(default=None, description='客户联系地址')
    customer_status: int | None = Field(default=None, description='客户状态：0 未设置')
    intent_status: int | None = Field(default=None, description='意向状态：0 未设置')
    contact_first: int | None = Field(default=None, description='第一联系人 id')
    admin_id: int | None = Field(default=None, description='录入人')
    belong_uid: int | None = Field(default=None, description='所属人')
    belong_did: int | None = Field(default=None, description='所属部门')
    belong_time: int | None = Field(default=None, description='获取时间')
    distribute_time: int | None = Field(default=None, description='最新分配时间')
    follow_time: int | None = Field(default=None, description='最新跟进时间')
    next_time: int | None = Field(default=None, description='下次跟进时间')
    discard_time: int | None = Field(default=None, description='废弃时间')
    share_ids: str | None = Field(default=None, description='共享人员，如:1,2,3')
    content: str | None = Field(default=None, description='客户描述')
    market: str | None = Field(default=None, description='主要经营业务')
    remark: str | None = Field(default=None, description='备注信息')
    tax_bank: str | None = Field(default=None, description='开户银行')
    tax_banksn: str | None = Field(default=None, description='银行帐号')
    tax_num: str | None = Field(default=None, description='纳税人识别号')
    tax_mobile: str | None = Field(default=None, description='开票电话')
    tax_address: str | None = Field(default=None, description='开票地址')
    is_lock: int | None = Field(default=None, description='锁定状态：0 未锁，1 已锁')
    create_time: int | None = Field(default=None, description='添加时间')
    update_time: int | None = Field(default=None, description='修改时间')
    delete_time: int | None = Field(default=None, description='删除时间')
    
    # 新增客户时传入的联系人信息（主要用于新增/编辑接口的输入）
    contact_info: Optional[CustomerContactInfoModel] = Field(default=None, description='客户联系人信息')
    
    # 客户联系人列表（用于详情接口返回）
    contact_list: list[dict] | None = Field(default=None, description='客户联系人列表')

    # 扩展字段，用于列表和详情展示
    belong_name: str | None = Field(default=None, description='所属人姓名')
    belong_department: str | None = Field(default=None, description='所属部门')
    industry: str | None = Field(default=None, description='所属行业')
    grade: str | None = Field(default=None, description='客户等级')
    source: str | None = Field(default=None, description='客户来源')
    customer_status_name: str | None = Field(default=None, description='客户状态名称')
    intent_status_name: str | None = Field(default=None, description='意向状态名称')
    follow_time_str: str | None = Field(default=None, description='最近跟进时间字符串')
    next_time_str: str | None = Field(default=None, description='下次跟进时间字符串')
    create_time_str: str | None = Field(default=None, description='创建时间字符串')
    belong_time_str: str | None = Field(default=None, description='获取时间字符串')
    distribute_time_str: str | None = Field(default=None, description='最新分配时间字符串')
    update_time_str: str | None = Field(default=None, description='修改时间字符串')
    contact_name: str | None = Field(default=None, description='联系人姓名')
    contact_mobile: str | None = Field(default=None, description='联系电话')
    contact_email: str | None = Field(default=None, description='联系人邮箱')
    share_names: str | None = Field(default=None, description='共享人员姓名列表')

    @Xss(field_name='name', message='客户名称不能包含脚本字符')
    @NotBlank(field_name='name', message='客户名称不能为空')
    @Size(field_name='name', min_length=0, max_length=255, message='客户名称长度不能超过 255 个字符')
    def get_name(self) -> str | None:
        return self.name

    @Xss(field_name='address', message='联系地址不能包含脚本字符')
    @Size(field_name='address', min_length=0, max_length=255, message='联系地址长度不能超过 255 个字符')
    def get_address(self) -> str | None:
        return self.address

    def validate_fields(self) -> None:
        self.get_name()


class CustomerPageQueryModel(CustomerModel):
    """
    客户分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    tab: int | None = Field(default=0, description='标签页：0 全部，1 我的客户，2 下属客户，3 分享客户')
    customer_status_filter: int | None = Field(default=None, description='客户状态筛选')
    industry_id_filter: int | None = Field(default=None, description='行业筛选')
    source_id_filter: int | None = Field(default=None, description='来源筛选')
    grade_id_filter: int | None = Field(default=None, description='等级筛选')
    intent_status_filter: int | None = Field(default=None, description='意向状态筛选')
    follow_time_start: int | None = Field(default=None, description='跟进开始时间')
    follow_time_end: int | None = Field(default=None, description='跟进结束时间')
    next_time_start: int | None = Field(default=None, description='下次跟进开始时间')
    next_time_end: int | None = Field(default=None, description='下次跟进结束时间')


class AddCustomerModel(CustomerModel):
    """
    新增客户模型
    """

    pass


class EditCustomerModel(AddCustomerModel):
    """
    编辑客户模型
    """

    pass


class DeleteCustomerModel(BaseModel):
    """
    删除客户模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的客户 ID')
