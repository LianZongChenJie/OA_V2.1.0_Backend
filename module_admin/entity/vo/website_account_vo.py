from typing import Optional, List
from pydantic import BaseModel, Field

# 基础查询模型
class PageQueryModel(BaseModel):
    """分页查询基础模型"""
    page_num: Optional[int] = Field(1, description='页码')
    page_size: Optional[int] = Field(10, description='每页数量')

# 网站账号基础模型
class WebsiteAccountModel(BaseModel):
    """网站账号信息基础模型"""
    id: Optional[int] = None
    website_name: Optional[str] = Field(None, description='网站名称', max_length=255)
    website_url: Optional[str] = Field(None, description='网址', max_length=1512)
    username: Optional[str] = Field(None, description='用户名', max_length=100)
    password: Optional[str] = Field(None, description='密码', max_length=100)
    has_uk: Optional[str] = Field(None, description='是否有 UK', max_length=200)
    remark: Optional[str] = Field(None, description='说明')
    sort: Optional[int] = Field(0, description='排序')
    created_at: Optional[str] = Field(None, description='创建时间')
    updated_at: Optional[str] = Field(None, description='更新时间')
    delete_time: Optional[int] = Field(0, description='删除时间')
    status: Optional[str] = Field(None, description='状态')
    create_time: Optional[int] = Field(None, description='创建时间戳')
    update_time: Optional[int] = Field(None, description='更新时间戳')

# 分页查询模型
class WebsiteAccountPageQueryModel(PageQueryModel):
    """网站账号信息分页查询模型"""
    website_url: Optional[str] = Field(None, description='网址（模糊查询）')

# 新增/编辑/删除模型
class AddWebsiteAccountModel(BaseModel):
    """新增网站账号信息模型"""
    website_name: str = Field(..., description='网站名称', max_length=255)
    website_url: str = Field(..., description='网址', max_length=1512)
    username: Optional[str] = Field(None, description='用户名', max_length=100)
    password: Optional[str] = Field(None, description='密码', max_length=100)
    has_uk: Optional[str] = Field(None, description='是否有 UK', max_length=200)
    remark: Optional[str] = Field(None, description='说明')
    sort: Optional[int] = Field(0, description='排序')
    status: Optional[str] = Field(None, description='状态')

class EditWebsiteAccountModel(WebsiteAccountModel):
    """编辑网站账号信息模型"""
    id: int = Field(..., description='网站账号 ID')

class DeleteWebsiteAccountModel(BaseModel):
    """删除网站账号信息模型"""
    ids: str = Field(..., description='网站账号 ID 列表（逗号分隔）')

class SetWebsiteAccountStatusModel(BaseModel):
    """设置网站账号状态模型"""
    id: int = Field(..., description='网站账号 ID')
    status: int = Field(..., description='状态（0-禁用，1-启用）')

# 导入相关模型
class WebsiteAccountImportResponseModel(BaseModel):
    """网站账号导入响应模型"""
    is_success: bool = Field(True, description='是否成功')
    message: str = Field('操作成功', description='响应信息')
    success_count: Optional[int] = Field(0, description='成功导入数量')
    fail_count: Optional[int] = Field(0, description='失败数量')
    fail_data: Optional[List[dict]] = Field([], description='失败数据及原因')

class WebsiteAccountImportTempModel(BaseModel):
    """网站账号导入临时模型（与 Excel 表头字段名一致）"""
    website_name: str = ''
    website_url: str = ''
    username: str = ''
    password: str = ''
    has_uk: str = ''
    sort: str = '0'
    remark: str = ''
