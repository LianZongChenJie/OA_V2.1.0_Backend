from email.policy import default

from pydantic import BaseModel, Field, validator, ConfigDict, field_serializer
from typing import Optional
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp

class OaFlowCateModel(BaseModel):
    """审批类型基础模型"""
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='主键id')
    title: str | None = Field(default=None, description='审批类型名称')
    name: str | None  = Field(default=None, description='审批类型标识,唯一')
    module_id: int | None = Field(default=None, description='关联审批模块id')
    check_table: str | None = Field(default=None, description='关联数据库表名')
    icon: str | None = Field(default=None, description='图标')
    department_ids: str | None = Field(default=None, description='应用部门ID（空为全部）1,2,3')
    sort: int | None = Field(default=None, description='排序：越大越靠前')
    is_copy: int | None = Field(default=None, description='是否支持抄送人')
    is_file: int | None = Field(default=None, description='审批过程是否支持上传附件')
    is_export: int | None = Field(default=None, description='审批通过后是否支持导出PDF打印')
    is_back: int | None = Field(default=None, description='是否支持撤回')
    is_reversed: int | None = Field(default=None, description='是否支持反确认')
    form: int | None = Field(default=None, description='预设字段，表单模式：1固定表单,2自定义表单')
    add_url: str | None = Field(default=None, description='新建链接：固定表单模式必填')
    view_url: str | None = Field(default=None, description='查看链接：固定表单模式必填')
    form_id: int | None = Field(default=None, description='表单id：自定义表单模式必填')
    is_list: int | None = Field(default=None, description='是否列表页显示：0不显示 1显示')
    status: int | None = Field(default=None, description='状态：-1删除 0禁用 1启用')
    template_id: int | None = Field(default=None, description='审批消息模板id')
    create_time: int | None = Field(default=None,  description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')


    @field_serializer('create_time')
    def serialize_create_time(self, value: Optional[int]) -> Optional[str]:
        """序列化创建时间"""
        return format_timestamp(value)

    @field_serializer('update_time')
    def serialize_update_time(self, value: Optional[int]) -> Optional[str]:
        """序列化更新时间"""
        return format_timestamp(value)

# class FlowCateQueryModel(OaFlowCateModel):
#     """
#     消息模板不分页查询模型
#     """
#
#     begin_time: str | None = Field(default=None, description='开始时间')
#     end_time: str | None = Field( description='结束时间')

class FlowCatePageQueryModel(OaFlowCateModel):
    """
    用户管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')

