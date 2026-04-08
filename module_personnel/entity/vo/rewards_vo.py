from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel
from decimal import Decimal
from utils.timeformat import format_timestamp
from pydantic import field_serializer
from typing import Optional,List
class OaRewardsBaseModel(BaseModel):
    """奖罚记录 VO - 用于数据展示"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None= Field(default=None, description='主键ID')
    uid: int | None= Field(default=None, description='员工ID')
    types: int | None= Field(default=None, description='奖罚类型')
    types_name: str | None = Field(None, description='奖罚类型名称')
    rewards_cate: int | None= Field(default=None, description='奖罚项目')
    rewards_cate_name: str | None = Field(None, description='奖罚项目名称')
    rewards_time: int | None= Field(default=None, description='奖罚日期')
    rewards_time_str: str | None = Field(None, description='奖罚日期（字符串格式）')
    cost: Decimal = Field(default=None, description='金额')
    cost_str: str | None = Field(None, description='金额字符串')
    thing: str = Field(default=None, description='物品')
    status: int | None= Field(default=None, description='状态')
    status_name: str | None = Field(None, description='状态名称')
    file_ids: str = Field(default=None, description='附件')
    file_ids_list: Optional[List[str]] = Field(None, description='附件列表')
    remark: str | None = Field(None, description='备注说明')
    admin_id: int | None= Field(default=None, description='创建人')
    create_time: int | None= Field(default=None, description='添加时间')
    create_time_str: str | None = Field(None, description='添加时间（字符串格式）')
    update_time: int | None= Field(default=None, description='修改时间')
    delete_time: int | None= Field(default=None, description='删除时间')

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)

    @field_serializer('delete_time')
    def serialize_delete_time(self, value: Optional[int]) -> Optional[str]:
        """序列化删除时间"""
        return format_timestamp(value)

class OaRewardsQueryModel(OaRewardsBaseModel):
    """奖罚记录 VO - 用于查询条件"""
    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')

class OaRewardsPageQueryModel(OaRewardsQueryModel):
    """奖罚记录分页查询VO"""
    page_num: int | None = Field(None, description='页码')
    page_size: int | None = Field(None, description='页大小')


    