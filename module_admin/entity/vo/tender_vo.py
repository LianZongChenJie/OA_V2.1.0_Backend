from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field
from fastapi import UploadFile

# 通用基础模型
T = TypeVar('T')

class PageQueryModel(BaseModel):
    """分页查询基础模型"""
    page_num: Optional[int] = Field(1, description='页码')
    page_size: Optional[int] = Field(10, description='每页数量')

class PageModel(BaseModel, Generic[T]):
    """分页结果基础模型"""
    total: int = Field(0, description='总记录数')
    rows: List[T] = Field([], description='数据列表')

class DataResponseModel(BaseModel):
    """数据响应基础模型"""
    code: int = Field(200, description='响应码')
    message: str = Field('success', description='响应信息')
    data: Optional[T] = None

class CrudResponseModel(BaseModel):
    """CRUD操作响应基础模型"""
    code: int = Field(200, description='响应码')
    message: str = Field('操作成功', description='响应信息')
    data: Optional[T] = None
    is_success: Optional[bool] = Field(True, description='是否成功')

# 投标信息基础模型
class TenderModel(BaseModel):
    """投标信息基础模型"""
    id: Optional[int] = None
    month: Optional[str] = Field(None, description='月份', max_length=20)
    customer_name: Optional[str] = Field(None, description='客户名称', max_length=100)
    project_name: Optional[str] = Field(None, description='项目名称', max_length=200)
    tender_leader: Optional[str] = Field(None, description='投标负责人', max_length=50)
    purchase_date: Optional[str] = Field(None, description='购买日期（YYYY-MM-DD）')
    tender_agency: Optional[str] = Field(None, description='招标机构', max_length=100)
    project_cycle: Optional[str] = Field(None, description='项目周期', max_length=50)
    shortlisted_countries: Optional[str] = Field(None, description='入围家数', max_length=20)
    budget_amount: Optional[float] = Field(None, description='预算金额（元）')
    bid_opening_date: Optional[str] = Field(None, description='开标日期（YYYY-MM-DD）')
    is_tender_submitted: Optional[str] = Field(None, description='是否投标（是/否）', max_length=20)
    non_tender_reason: Optional[str] = Field(None, description='未投原因', max_length=200)
    tender_document_fee: Optional[float] = Field(None, description='标书款（元）')
    has_tender_invoice: Optional[str] = Field(None, description='标书款发票（是/否）', max_length=20)
    is_deposit_paid: Optional[str] = Field(None, description='是否缴纳保证金（是/否）', max_length=20)
    tender_deposit: Optional[float] = Field(None, description='投标保证金（元）')
    deposit_account_name: Optional[str] = Field(None, description='保证金账户名', max_length=100)
    deposit_bank: Optional[str] = Field(None, description='保证金开户行', max_length=100)
    deposit_account_no: Optional[str] = Field(None, description='保证金账号', max_length=50)
    is_deposit_refunded: Optional[str] = Field(None, description='是否退回保证金（是/否）', max_length=20)
    bid_result: Optional[str] = Field(None, description='中标结果', max_length=20)
    bid_service_fee: Optional[float] = Field(None, description='中标服务费（元）')
    sort: Optional[int] = Field(None, description='排序')
    create_time: Optional[str] = Field(None, description='创建时间（YYYY-MM-DD HH:MM:SS）')
    update_time: Optional[str] = Field(None, description='更新时间（YYYY-MM-DD HH:MM:SS）')
    delete_time: Optional[int] = Field(0, description='删除时间（时间戳）')

# 分页查询模型
class TenderPageQueryModel(PageQueryModel):
    """投标信息分页查询模型"""
    month: Optional[str] = Field(None, description='月份')
    customer_name: Optional[str] = Field(None, description='客户名称')
    project_name: Optional[str] = Field(None, description='项目名称')
    tender_leader: Optional[str] = Field(None, description='投标负责人')
    is_tender_submitted: Optional[str] = Field(None, description='是否投标')
    bid_result: Optional[str] = Field(None, description='中标结果')
    begin_time: Optional[str] = Field(None, description='开始时间（YYYY-MM-DD）')
    end_time: Optional[str] = Field(None, description='结束时间（YYYY-MM-DD）')

# 新增/编辑/删除模型
class AddTenderModel(TenderModel):
    """新增投标信息模型"""
    pass

class EditTenderModel(TenderModel):
    """编辑投标信息模型"""
    id: int = Field(..., description='投标ID')

class DeleteTenderModel(BaseModel):
    """删除投标信息模型"""
    ids: str = Field(..., description='投标ID列表（逗号分隔）')

# 附件相关模型
class TenderAttachmentModel(BaseModel):
    """投标附件基础模型"""
    id: Optional[int] = None
    project_tender_id: Optional[int] = None
    file_name: Optional[str] = Field(None, description='附件名称', max_length=200)
    file_path: Optional[str] = Field(None, description='附件路径', max_length=500)
    file_size: Optional[int] = Field(None, description='文件大小（字节）')  # 适配数据库int类型
    file_ext: Optional[str] = Field(None, description='文件扩展名', max_length=20)
    file_mime: Optional[str] = Field(None, description='文件MIME类型', max_length=100)
    sort: Optional[int] = Field(None, description='排序')
    # create_by: Optional[str] = Field(None, description='创建人（预留字段）', max_length=50)
    # create_time: Optional[str] = Field(None, description='创建时间（数据库自动填充）')
    # update_by: Optional[str] = Field(None, description='更新人（预留字段）', max_length=50)
    # update_time: Optional[str] = Field(None, description='更新时间（数据库自动填充）')
    delete_time: Optional[int] = Field(0, description='删除时间（时间戳）')

class AddTenderAttachmentModel(TenderAttachmentModel):
    """新增投标附件模型"""
    project_tender_id: int = Field(..., description='投标ID')
    file_name: str = Field(..., description='附件名称', max_length=200)
    file_path: str = Field(..., description='附件路径', max_length=500)

class DeleteTenderAttachmentModel(BaseModel):
    """删除投标附件模型"""
    ids: str = Field(..., description='附件ID列表（逗号分隔）')

# 导入相关模型
class TenderImportTemplateResponseModel(BaseModel):
    """投标导入模板下载响应模型"""
    file_url: Optional[str] = Field(None, description='模板文件下载链接')
    file_name: Optional[str] = Field(None, description='模板文件名')

class TenderImportResponseModel(CrudResponseModel):
    """投标导入响应模型"""
    success_count: Optional[int] = Field(0, description='成功导入数量')
    fail_count: Optional[int] = Field(0, description='失败数量')
    fail_data: Optional[List[dict]] = Field([], description='失败数据及原因')

class TenderImportTempModel(BaseModel):
    """投标导入临时模型（与Excel表头字段名完全一致）"""
    # 必填字段（无默认值）
    month: str
    customer_name: str
    project_name: str
    is_tender_submitted: str
    # 非必填字段（加默认值）
    tender_leader: str = ''
    purchase_date: str = ''
    tender_agency: str = ''
    project_cycle: str = ''
    shortlisted_countries: str = ''
    budget_amount: str = ''
    bid_opening_date: str = ''
    non_tender_reason: str = ''
    tender_document_fee: str = ''
    has_tender_invoice: str = ''
    is_deposit_paid: str = ''
    tender_deposit: str = ''
    deposit_account_name: str = ''
    deposit_bank: str = ''
    deposit_account_no: str = ''
    is_deposit_refunded: str = ''
    bid_result: str = ''
    bid_service_fee: str = ''
    sort: str = '0'

# 响应模型
class TenderDetailModel(DataResponseModel):
    """投标信息详情返回模型"""
    data: Optional[TenderModel] = None

class TenderListModel(PageModel):
    """投标信息列表返回模型"""
    data: list = []

class TenderResponseModel(CrudResponseModel):
    """投标信息操作返回模型"""
    data: Optional[TenderModel] = None

class TenderAttachmentListModel(DataResponseModel):
    """投标附件列表返回模型"""
    data: List[TenderAttachmentModel] = Field([], description='附件列表')

# 附件上传模型
class UploadTenderAttachmentModel(BaseModel):
    """投标附件上传模型"""
    project_tender_id: int = Field(..., description='投标ID')
    sort: Optional[int] = Field(0, description='排序值')