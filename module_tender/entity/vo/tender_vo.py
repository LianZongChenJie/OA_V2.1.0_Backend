"""
招标文件智能生成模块相关 Pydantic 模型
"""
from typing import List
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TenderRequirementModel(BaseModel):
    """招标要求明细模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=0, description='ID')
    tender_id: int | None = Field(default=0, description='关联招标文件ID')
    requirement_type: str | None = Field(default='', description='要求类型:学历/工作/技能/证书/业绩')
    requirement_key: str | None = Field(default='', description='要求键')
    operator: str | None = Field(default='', description='运算符:eq/gte/lte/contains/in')
    requirement_value: str | None = Field(default='', description='要求值')
    score_weight: float | None = Field(default=0, description='评分权重')
    description: str | None = Field(default='', description='要求描述')
    create_time: int | None = Field(default=0, description='创建时间')


class BidPersonnelMappingModel(BaseModel):
    """投标人员映射模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=0, description='ID')
    tender_id: int | None = Field(default=0, description='关联招标文件ID')
    resume_id: int | None = Field(default=0, description='简历ID')
    match_score: float | None = Field(default=0, description='匹配得分')
    match_reason: str | None = Field(default='', description='匹配原因')
    sort_order: int | None = Field(default=0, description='排序序号')
    is_selected: int | None = Field(default=0, description='是否选中:1选中,0推荐中')
    create_time: int | None = Field(default=0, description='创建时间')
    # 关联展示字段
    resume_name: str | None = Field(default='', description='简历姓名')
    resume_gender: str | None = Field(default='', description='性别')
    resume_age: int | None = Field(default=0, description='年龄')
    resume_education: str | None = Field(default='', description='学历')
    resume_work_years: int | None = Field(default=0, description='工作年限')
    resume_current_company: str | None = Field(default='', description='当前公司')
    resume_current_position: str | None = Field(default='', description='当前职位')
    resume_skills: str | None = Field(default='', description='技能标签')
    resume_certificates: str | None = Field(default='', description='证书')


class TenderDocumentModel(BaseModel):
    """招标文件信息模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=0, description='ID')
    tender_uuid: str | None = Field(default='', description='招标文件UUID')
    file_name: str | None = Field(default='', description='原始文件名')
    tender_name: str | None = Field(default='', description='招标项目名称')
    tender_code: str | None = Field(default='', description='招标编号')
    company_name: str | None = Field(default='', description='招标单位')
    total_pages: int | None = Field(default=0, description='总页数')
    status: int | None = Field(default=0, description='状态:0已解析,1匹配中,2已完成')
    requirements_json: str | None = Field(default='', description='人员配置要求JSON')
    score_standard_json: str | None = Field(default='', description='评标标准JSON')
    file_path: str | None = Field(default='', description='原始文件路径')
    generated_file_path: str | None = Field(default='', description='生成的投标文件路径')
    admin_id: int | None = Field(default=0, description='创建人')
    create_time: int | None = Field(default=0, description='创建时间')
    update_time: int | None = Field(default=0, description='更新时间')


class TenderDocumentPageQueryModel(BaseModel):
    """招标文件分页查询模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页条数')
    tender_name: str | None = Field(default=None, description='招标项目名称')
    tender_code: str | None = Field(default=None, description='招标编号')
    company_name: str | None = Field(default=None, description='招标单位')


class TenderDocumentUploadResultModel(BaseModel):
    """招标文件上传解析结果模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    tender_id: int = Field(default=0, description='招标文件ID')
    tender_uuid: str = Field(default='', description='招标文件UUID')
    tender_name: str = Field(default='', description='招标项目名称')
    tender_code: str = Field(default='', description='招标编号')
    requirement_count: int = Field(default=0, description='提取要求条数')
    message: str = Field(default='', description='处理结果消息')


class TenderDocumentDetailModel(BaseModel):
    """招标文件详情模型（含要求列表）"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    tender: TenderDocumentModel | None = Field(default=None, description='招标文件信息')
    requirements: List[TenderRequirementModel] = Field(default=[], description='要求明细列表')


class MatchResultModel(BaseModel):
    """匹配结果模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    tender_id: int = Field(default=0, description='招标文件ID')
    total_candidates: int = Field(default=0, description='候选人数')
    matched_count: int = Field(default=0, description='匹配人数')
    selected_count: int = Field(default=0, description='已选人数')
    match_list: List[BidPersonnelMappingModel] = Field(default=[], description='匹配列表')


class SelectPersonnelModel(BaseModel):
    """选择人员请求模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    mapping_id: int = Field(description='映射ID')
    is_selected: int = Field(description='是否选中:1选中,0取消')


class GenerateBidFileModel(BaseModel):
    """生成投标文件请求模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    tender_id: int = Field(description='招标文件ID')
    output_format: str = Field(default='docx', description='输出格式:docx/pdf')
