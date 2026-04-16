from typing import Any, Literal

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class ContractModel(BaseModel):
    """
    销售合同表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='合同 ID')
    pid: int | None = Field(default=None, description='父协议 id')
    code: str | None = Field(default=None, description='合同编号')
    name: str | None = Field(default=None, description='合同名称')
    cate_id: int | None = Field(default=None, description='分类 id')
    types: int | None = Field(default=None, description='合同性质:1 普通合同 2 商品合同 3 服务合同')
    subject_id: str | None = Field(default=None, description='签约主体')
    customer_id: int | None = Field(default=None, description='关联客户 ID，预设数据')
    chance_id: int | None = Field(default=None, description='销售机会 id')
    customer: str | None = Field(default=None, description='客户名称')
    contact_name: str | None = Field(default=None, description='客户代表')
    contact_mobile: str | None = Field(default=None, description='客户电话')
    contact_address: str | None = Field(default=None, description='客户地址')
    start_time: int | None = Field(default=None, description='合同开始时间')
    end_time: int | None = Field(default=None, description='合同结束时间')
    admin_id: int | None = Field(default=None, description='创建人')
    prepared_uid: int | None = Field(default=None, description='合同制定人')
    sign_uid: int | None = Field(default=None, description='合同签订人')
    keeper_uid: int | None = Field(default=None, description='合同保管人')
    share_ids: str | None = Field(default=None, description='共享人员，如:1,2,3')
    file_ids: str | None = Field(default=None, description='相关附件，如:1,2,3')
    seal_ids: str | None = Field(default=None, description='盖章合同附件，如:1,2,3')
    sign_time: int | None = Field(default=None, description='合同签订时间')
    did: int | None = Field(default=None, description='合同所属部门')
    cost: float | None = Field(default=None, description='合同金额')
    content: str | None = Field(default=None, description='合同内容')
    is_tax: int | None = Field(default=None, description='是否含税：0 未含税，1 含税')
    tax: float | None = Field(default=None, description='税点')
    stop_uid: int | None = Field(default=None, description='中止人')
    stop_time: int | None = Field(default=None, description='中止时间')
    void_uid: int | None = Field(default=None, description='作废人')
    void_time: int | None = Field(default=None, description='作废时间')
    archive_uid: int | None = Field(default=None, description='归档人')
    archive_time: int | None = Field(default=None, description='归档时间')
    remark: str | None = Field(default=None, description='备注信息')
    create_time: int | None = Field(default=None, description='添加时间')
    update_time: int | None = Field(default=None, description='修改时间')
    delete_time: int | None = Field(default=None, description='删除时间')
    check_status: int | None = Field(default=None, description='审核状态:0 待审核，1 审核中，2 审核通过，3 审核不通过，4 撤销审核')
    check_flow_id: int | None = Field(default=None, description='审核流程 id')
    check_step_sort: int | None = Field(default=None, description='当前审批步骤')
    check_uids: str | None = Field(default=None, description='当前审批人 ID，如:1,2,3')
    check_last_uid: str | None = Field(default=None, description='上一审批人')
    check_history_uids: str | None = Field(default=None, description='历史审批人 ID，如:1,2,3')
    check_copy_uids: str | None = Field(default=None, description='抄送人 ID，如:1,2,3')
    check_time: int | None = Field(default=None, description='审核通过时间')

    # 扩展字段，用于列表展示
    cate_title: str | None = Field(default=None, description='分类名称')
    subject_title: str | None = Field(default=None, description='签约主体名称')
    admin_name: str | None = Field(default=None, description='创建人姓名')
    prepared_name: str | None = Field(default=None, description='合同制定人姓名')
    sign_name: str | None = Field(default=None, description='合同签订人姓名')
    keeper_name: str | None = Field(default=None, description='合同保管人姓名')
    share_names: list[str] | None = Field(default=None, description='共享人员姓名列表')
    check_status_name: str | None = Field(default=None, description='审核状态名称')
    start_time_str: str | None = Field(default=None, description='合同开始时间字符串')
    end_time_str: str | None = Field(default=None, description='合同结束时间字符串')
    sign_time_str: str | None = Field(default=None, description='合同签订时间字符串')
    create_time_str: str | None = Field(default=None, description='创建时间字符串')
    update_time_str: str | None = Field(default=None, description='更新时间字符串')
    stop_time_str: str | None = Field(default=None, description='中止时间字符串')
    void_time_str: str | None = Field(default=None, description='作废时间字符串')
    archive_time_str: str | None = Field(default=None, description='归档时间字符串')
    check_time_str: str | None = Field(default=None, description='审核通过时间字符串')
    
    # 列表专用字段（驼峰命名）
    cate_name: str | None = Field(default=None, description='分类名称')
    subject_name: str | None = Field(default=None, description='签约主体名称')
    admin_name_camel: str | None = Field(default=None, alias='adminName', description='创建人姓名')
    prepared_name_camel: str | None = Field(default=None, alias='preparedName', description='合同制定人姓名')
    dept_name: str | None = Field(default=None, alias='deptName', description='所属部门名称')

    @field_validator('start_time', 'end_time', 'sign_time', 'stop_time', 'void_time', 'archive_time', 'check_time', mode='before')
    @classmethod
    def validate_time_fields(cls, value: Any) -> int | None:
        """
        验证并转换时间字段，支持时间戳和日期字符串
        """
        if value is None or value == '' or value == 0:
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp())
            except ValueError:
                try:
                    return int(value)
                except ValueError:
                    pass

        return value

    @Xss(field_name='name', message='合同名称不能包含脚本字符')
    @NotBlank(field_name='name', message='合同名称不能为空')
    @Size(field_name='name', min_length=0, max_length=255, message='合同名称长度不能超过 255 个字符')
    def get_name(self) -> str | None:
        return self.name

    @Xss(field_name='code', message='合同编号不能包含脚本字符')
    @Size(field_name='code', min_length=0, max_length=255, message='合同编号长度不能超过 255 个字符')
    def get_code(self) -> str | None:
        return self.code

    @Xss(field_name='customer', message='客户名称不能包含脚本字符')
    @Size(field_name='customer', min_length=0, max_length=255, message='客户名称长度不能超过 255 个字符')
    def get_customer(self) -> str | None:
        return self.customer

    @Xss(field_name='contact_name', message='客户代表不能包含脚本字符')
    @Size(field_name='contact_name', min_length=0, max_length=255, message='客户代表长度不能超过 255 个字符')
    def get_contact_name(self) -> str | None:
        return self.contact_name

    @Xss(field_name='contact_address', message='客户地址不能包含脚本字符')
    @Size(field_name='contact_address', min_length=0, max_length=255, message='客户地址长度不能超过 255 个字符')
    def get_contact_address(self) -> str | None:
        return self.contact_address

    @Xss(field_name='content', message='合同内容不能包含脚本字符')
    @Size(field_name='content', min_length=0, max_length=16777215, message='合同内容长度超出限制')
    def get_content(self) -> str | None:
        return self.content

    @Xss(field_name='remark', message='备注信息不能包含脚本字符')
    @Size(field_name='remark', min_length=0, max_length=16777215, message='备注信息长度超出限制')
    def get_remark(self) -> str | None:
        return self.remark

    def validate_fields(self) -> None:
        self.get_name()
        self.get_code()
        self.get_customer()
        self.get_contact_name()
        self.get_contact_address()
        self.get_content()
        self.get_remark()


class ContractPageQueryModel(ContractModel):
    """
    销售合同分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    tab: int | None = Field(default=0, description='标签页：0 全部，1 待我审核，2 我已审核')
    types_filter: int | None = Field(default=None, description='合同性质筛选')
    cate_id_filter: int | None = Field(default=None, description='分类筛选')
    check_status_filter: int | None = Field(default=None, description='审核状态筛选')
    sign_time_start: int | None = Field(default=None, description='签订开始时间')
    sign_time_end: int | None = Field(default=None, description='签订结束时间')
    end_time_start: int | None = Field(default=None, description='结束开始时间')
    end_time_end: int | None = Field(default=None, description='结束结束时间')
    admin_id_filter: int | None = Field(default=None, description='创建人 ID 筛选')
    archive_status: int | None = Field(default=0, description='归档状态：0 正常，1 已归档')
    stop_status: int | None = Field(default=0, description='中止状态：0 正常，1 已中止')
    void_status: int | None = Field(default=0, description='作废状态：0 正常，1 已作废')


class AddContractModel(ContractModel):
    """
    新增销售合同模型
    """

    pass


class EditContractModel(AddContractModel):
    """
    编辑销售合同模型
    """

    pass


class DeleteContractModel(BaseModel):
    """
    删除销售合同模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int = Field(description='需要删除的合同 ID')

