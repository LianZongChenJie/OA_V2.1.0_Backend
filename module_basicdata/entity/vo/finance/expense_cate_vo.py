from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
class OaExpenseCateBaseModel(BaseModel):
    """报销类型基础VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    title: str | None = Field(None, description='报销类型名称')
    status: int | None = Field(None, description='状态：-1删除 0禁用 1启用')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')
    delete_time: int | None = Field(None, description='删除时间')


class ExpenseCatePageQueryModel(OaExpenseCateBaseModel):

    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')
