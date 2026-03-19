from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp
from typing import Optional
class FlowModuleModel(BaseModel):

    """审批模块VO"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)
    id: int | None = Field(default=None, description='主键id')
    title: str | None = Field(default=None, max_length=100, description='审批模块名称')
    icon: str | None = Field(default=None, max_length=255, description='预设字段，图标')
    sort: int | None = Field(default=None, description='排序：越大越靠前')
    department_ids: str | None = Field(default=None, max_length=255, description='应用部门ID（空为全部）1,2,3')
    status: int | None = Field(default=None, ge=-1, le=1, description='状态：-1删除 0禁用 1启用')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')

    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)


    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'icon': self.icon,
            'sort': self.sort,
            'department_ids': self.department_ids,
            'status': self.status,
            'create_time': self.create_time,
            'update_time': self.update_time
        }

class FlowModuleQueryModel(FlowModuleModel):
    """
    消息模板不分页查询模型
    """

    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')

class FlowModulePageQueryModel(FlowModuleQueryModel):
    """
    用户管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')

