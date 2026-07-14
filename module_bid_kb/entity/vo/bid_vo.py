"""
投标文件知识库相关 Pydantic 模型
"""
from typing import List
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from module_resume_kb.entity.vo.resume_vo import ResumeModel


class BidDocumentModel(BaseModel):
    """投标文件信息模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=0, description='ID')
    bid_uuid: str | None = Field(default='', description='投标文件UUID')
    file_name: str | None = Field(default='', description='原始文件名')
    bid_name: str | None = Field(default='', description='投标项目名称')
    bid_code: str | None = Field(default='', description='项目编号')
    company_name: str | None = Field(default='', description='投标公司')
    total_pages: int | None = Field(default=0, description='总页数')
    resume_count: int | None = Field(default=0, description='包含简历数量')
    status: int | None = Field(default=1, description='状态: 0处理中,1完成,2失败,9删除')
    parse_status: int | None = Field(default=1, description='解析状态: 0处理中,1完成,2失败')
    parse_progress: int | None = Field(default=100, description='解析进度百分比')
    parse_message: str | None = Field(default='', description='解析状态消息')
    admin_id: int | None = Field(default=0, description='创建人')
    create_time: int | None = Field(default=0, description='创建时间')
    update_time: int | None = Field(default=0, description='更新时间')


class BidDocumentPageQueryModel(BaseModel):
    """投标文件分页查询模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页条数')
    bid_name: str | None = Field(default=None, description='投标项目名称')
    bid_code: str | None = Field(default=None, description='项目编号')
    company_name: str | None = Field(default=None, description='投标公司')


class BidDocumentUploadResultModel(BaseModel):
    """投标文件上传结果模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    bid_id: int = Field(default=0, description='投标文件ID')
    bid_uuid: str = Field(default='', description='投标文件UUID')
    bid_name: str = Field(default='', description='投标项目名称')
    bid_code: str = Field(default='', description='项目编号')
    resume_count: int = Field(default=0, description='成功解析简历数量')
    failed_count: int = Field(default=0, description='解析失败数量')
    message: str = Field(default='', description='处理结果消息')


class BidDocumentDetailModel(BaseModel):
    """投标文件详情模型（含关联简历列表）"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    bid: BidDocumentModel | None = Field(default=None, description='投标文件信息')
    resume_list: List[ResumeModel] = Field(default=[], description='关联简历列表')
