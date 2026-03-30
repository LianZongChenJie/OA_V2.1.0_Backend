from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AdminImportTempModel(BaseModel):
    """员工导入临时模型（与 Excel 表头字段名完全一致）"""
    # 必填字段
    name: str = Field(..., description='姓名')
    mobile: str = Field(..., description='手机号码')

    # 非必填字段
    email: str = ''
    sex: str = '未知'
    department: str = ''
    position: str = ''
    type: str = '未知'
    entry_time: str = ''


class CustomerImportTempModel(BaseModel):
    """客户导入临时模型（与 Excel 表头字段名完全一致）"""
    # 必填字段
    name: str = Field(..., description='客户名称')
    c_name: str = Field(..., description='联系人姓名')
    c_mobile: str = Field(..., description='联系人手机')

    # 非必填字段
    source: str = ''
    grade: str = ''
    industry: str = ''
    tax_num: str = ''
    tax_bank: str = ''
    tax_banksn: str = ''
    tax_mobile: str = ''
    tax_address: str = ''
    address: str = ''
    content: str = ''
    market: str = ''


class ImportResponseModel(BaseModel):
    """导入响应模型"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    is_success: bool = True
    message: str = ''
    success_count: int = 0
    fail_count: int = 0
    fail_data: list[dict] | None = None
