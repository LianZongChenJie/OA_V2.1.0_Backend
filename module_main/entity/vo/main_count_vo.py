from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic import field_serializer
class CountBaseModel(BaseModel):
    """统计信息基类"""
    expense: int | None = Field(None, description='报销总数')
    invoice: int | None = Field(None, description='开票总数')
    ticket: int | None = Field(None, description='收票总数')
    customer: int | None = Field(None, description='客户总数')
    contract: int | None = Field(None, description='销售合同总数')
    purchase: int | None = Field(None, description='采购合同总数')
    project: int | None = Field(None, description='项目合同总数')
    projectTask: int | None = Field(None, description='项目任务总数')


class AwaitReviewBaseModel(BaseModel):
    """待审核信息基类"""
    officialDoc: int | None = Field(None, description='待审核公文总数')
    seal: int | None = Field(None, description='待审核公章总数')
    contract: int | None = Field(None, description='待审核销售合同总数')
    purchase: int | None = Field(None, description='待审核采购合同总数')
    expense: int | None = Field(None, description='待审核报销总数')
    invoice: int | None = Field(None, description='待审核开票总数')
    ticket: int | None = Field(None, description='待审核收票总数')
    project: int | None = Field(None, description='待审核项目合同总数')
    projectTask: int | None = Field(None, description='待审核项目任务总数')

