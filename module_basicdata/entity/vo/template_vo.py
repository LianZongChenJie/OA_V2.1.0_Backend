from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional
from pydantic.alias_generators import to_camel


class TemplateBaseModel(BaseModel):
    """基础模板模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    id: int | None = Field(default=None, description='主键id')
    title: str | None = Field(default=None, max_length=255, description='消息模板名称')
    name: str | None = Field(default=None, max_length=255, description='权限标识唯一')
    types: int | None = Field(default=None, ge=1, le=2, description='类型:1普通消息,2审批消息')
    check_types: int | None = Field(default=None, description='审批类型:0')
    remark: str | None = Field(default=None, max_length=500, description='备注描述，使用场景等')
    msg_link: str | None = Field(default=None, max_length=255, description='消息模板链接(审批申请)')
    msg_title_0: str | None = Field(default=None, max_length=255, description='消息模板标题(审批申请发审批人)')
    msg_content_0: str | None = Field(default=None, max_length=500, description='消息模板内容(审批申请发审批人)')
    msg_title_1: str | None = Field(default=None, max_length=255, description='消息模板标题(审批通过发申请人)')
    msg_content_1: str | None = Field(default=None, max_length=500, description='消息模板内容(审批通过发申请人)')
    msg_title_2: str | None = Field(default=None, max_length=255, description='消息模板标题(审批拒绝发申请人)')
    msg_content_2: str | None = Field(default=None, max_length=500, description='消息模板内容(审批拒绝发申请人)')
    msg_title_3: str | None = Field(default=None, max_length=255, description='消息模板标题(审批通过发抄送人)')
    msg_content_3: str | None = Field(default=None, max_length=500, description='消息模板内容(审批通过发抄送人)')
    email_link: str | None = Field(default=None, max_length=255, description='邮箱消息模板链接')
    status: int | None = Field(default=None, ge=-1, le=1, description='状态：-1删除 0禁用 1启用')
    admin_id: str | None = Field(default=None, description='创建人')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')




class TemplateCreateModel(TemplateBaseModel):
    """创建模板请求模型"""
    pass

class TemplateRowModel(TemplateBaseModel):
    """
    模板行数据模型
    """
    pass

class TemplateQueryModel(TemplateBaseModel):
    """
    用户管理不分页查询模型
    """

    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')

class TemplatePageQueryModel(TemplateQueryModel):
    """
    用户管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class TemplateUpdateModel(BaseModel):
    """更新模板请求模型"""
    title: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    types: Optional[int] = Field(None, ge=1, le=2)
    check_types: Optional[int] = None
    remark: Optional[str] = Field(None, max_length=500)
    msg_link: Optional[str] = Field(None, max_length=255)
    msg_title_0: Optional[str] = Field(None, max_length=255)
    msg_content_0: Optional[str] = Field(None, max_length=500)
    msg_title_1: Optional[str] = Field(None, max_length=255)
    msg_content_1: Optional[str] = Field(None, max_length=500)
    msg_title_2: Optional[str] = Field(None, max_length=255)
    msg_content_2: Optional[str] = Field(None, max_length=500)
    msg_title_3: Optional[str] = Field(None, max_length=255)
    msg_content_3: Optional[str] = Field(None, max_length=500)
    email_link: Optional[str] = Field(None, max_length=255)
    status: Optional[int] = Field(None, ge=-1, le=1)

    @validator('name')
    def validate_name(cls, v):
        if v and not v.isalpha():
            raise ValueError('name只能包含字母')
        return v


class TemplateResponseModel(TemplateBaseModel):
    """模板响应模型"""
    id: int
    create_time: int
    update_time: int
    delete_time: int

    class Config:
        orm_mode = True


class TemplateQueryParams(BaseModel):
    """模板查询参数模型"""
    page: int = Field(1, ge=1, description='页码')
    page_size: int = Field(20, ge=1, le=100, description='每页数量')
    title: Optional[str] = Field(None, description='模板名称模糊搜索')
    name: Optional[str] = Field(None, description='权限标识精确搜索')
    types: Optional[int] = Field(None, ge=1, le=2, description='类型筛选')
    status: Optional[int] = Field(None, ge=-1, le=1, description='状态筛选')