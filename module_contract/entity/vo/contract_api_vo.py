from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SetStopModel(BaseModel):
    """
    设置合同中止请求模型
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    type: str = Field(description='合同类型：sale(销售) | purchase(采购)')
    id: int = Field(description='合同ID')
    stop_status: int = Field(description='中止状态：1(中止) | 0(反中止)')
    stop_remark: str | None = Field(default=None, description='中止备注（中止时必填）')


class SetVoidModel(BaseModel):
    """
    设置合同作废请求模型
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    type: str = Field(description='合同类型：sale(销售) | purchase(采购)')
    id: int = Field(description='合同ID')
    void_status: int = Field(description='作废状态：1(作废) | 0(反作废)')
    void_remark: str | None = Field(default=None, description='作废备注（作废时必填）')