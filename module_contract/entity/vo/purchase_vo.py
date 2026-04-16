from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class PurchaseBaseModel(BaseModel):
    """
    采购合同基础模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='ID')
    pid: int = Field(default=0, description='父协议 id')
    code: str = Field(default='', description='合同编号')
    name: str = Field(default='', description='合同名称')
    cate_id: int = Field(default=0, description='分类 id')
    types: int = Field(default=1, description='合同性质:1 普通采购 2 物品采购 3 服务采购')
    subject_id: str = Field(default='', description='签约主体')
    supplier_id: int = Field(default=0, description='关联供应商 ID')
    supplier: str = Field(default='', description='供应商名称')
    contact_name: str = Field(default='', description='供应商代表')
    contact_mobile: str = Field(default='', description='供应商电话')
    contact_address: str = Field(default='', description='供应商地址')
    start_time: int = Field(default=0, description='合同开始时间')
    end_time: int = Field(default=0, description='合同结束时间')
    admin_id: int = Field(default=0, description='创建人')
    prepared_uid: int = Field(default=0, description='合同制定人')
    sign_uid: int = Field(default=0, description='合同签订人')
    keeper_uid: int = Field(default=0, description='合同保管人')
    share_ids: str = Field(default='', description='共享人员')
    file_ids: str = Field(default='', description='相关附件')
    seal_ids: str = Field(default='', description='盖章合同附件')
    sign_time: int = Field(default=0, description='合同签订时间')
    did: int = Field(default=0, description='合同所属部门')
    cost: float = Field(default=0.00, description='合同金额')
    content: str | None = Field(default=None, description='合同内容')
    stop_uid: int = Field(default=0, description='中止人')
    stop_time: int = Field(default=0, description='中止时间')
    stop_remark: str | None = Field(default=None, description='中止备注信息')
    void_uid: int = Field(default=0, description='作废人')
    void_time: int = Field(default=0, description='作废时间')
    void_remark: str | None = Field(default=None, description='作废备注信息')
    archive_uid: int = Field(default=0, description='归档人')
    archive_time: int = Field(default=0, description='归档时间')
    remark: str | None = Field(default=None, description='备注信息')
    create_time: int = Field(default=0, description='添加时间')
    update_time: int = Field(default=0, description='修改时间')
    delete_time: int = Field(default=0, description='删除时间')
    check_status: int = Field(default=0, description='审核状态')
    check_flow_id: int = Field(default=0, description='审核流程 id')
    check_step_sort: int = Field(default=0, description='当前审批步骤')
    check_uids: str = Field(default='', description='当前审批人 ID')
    check_last_uid: str = Field(default='', description='上一审批人')
    check_history_uids: str = Field(default='', description='历史审批人 ID')
    check_copy_uids: str = Field(default='', description='抄送人 ID')
    check_time: int = Field(default=0, description='审核通过时间')

    @field_validator('types', mode='before')
    @classmethod
    def validate_types(cls, value: Any) -> int:
        """验证并转换 types 字段"""
        if value is None:
            return 1
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except (ValueError, TypeError):
                return 1
        return 1

    @field_validator('start_time', 'end_time', 'sign_time', mode='before')
    @classmethod
    def validate_time_fields(cls, value: Any) -> int:
        """验证并转换时间字段"""
        if value is None or value == '' or value == 0:
            return 0
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            from datetime import datetime
            try:
                dt = datetime.strptime(value, '%Y-%m-%d')
                return int(dt.timestamp())
            except (ValueError, TypeError):
                return 0
        
        return 0


class AddPurchaseModel(PurchaseBaseModel):
    """
    新增采购合同模型
    """

    pass


class EditPurchaseModel(PurchaseBaseModel):
    """
    编辑采购合同模型
    """

    pass


class DeletePurchaseModel(BaseModel):
    """
    删除采购合同模型
    """

    id: int = Field(description='采购合同 ID')


class PurchasePageQueryModel(PurchaseBaseModel):
    """
    采购合同分页查询模型
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


class PurchaseModel(PurchaseBaseModel):
    """
    采购合同返回模型
    """

    cateName: str | None = Field(default=None, description='分类名称')
    adminName: str | None = Field(default=None, description='创建人姓名')
    preparedName: str | None = Field(default=None, description='制定人姓名')
    deptName: str | None = Field(default=None, description='部门名称')
    signName: str | None = Field(default=None, description='签订人姓名')
    keeperName: str | None = Field(default=None, description='保管人姓名')

    startTimeStr: str | None = Field(default=None, description='开始时间字符串')
    endTimeStr: str | None = Field(default=None, description='结束时间字符串')
    signTimeStr: str | None = Field(default=None, description='签订时间字符串')
    createTimeStr: str | None = Field(default=None, description='创建时间字符串')
    updateTimeStr: str | None = Field(default=None, description='更新时间字符串')

