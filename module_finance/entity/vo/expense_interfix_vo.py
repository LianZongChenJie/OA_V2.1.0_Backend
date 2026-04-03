from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp, int_time
from decimal import Decimal


class OaExpenseInterfixBaseModel(BaseModel):
    """报销关联数据基础VO"""
    id: int | None = Field(None, description='ID')
    exid: int | None = Field(None, description='报销ID')
    amount: Decimal | None = Field(None, description='金额')
    cate_id: int | None = Field(None, description='报销类型ID')
    cate_name: str | None = Field(None, description='报销类型名称')
    remarks: str | None = Field(None, description='备注')
    admin_id: int | None = Field(None, description='登记人')
    create_time: int | None = Field(None, description='创建时间')
    update_time: int | None = Field(None, description='更新时间')


    @field_serializer('create_time')
    def serialize_create_time(self, value: int) -> str:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: int) -> str:
        """序列化更新时间"""
        return format_timestamp(value)
