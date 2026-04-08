"""
网盘分享空间相关 Pydantic 模型
"""
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class DiskGroupModel(BaseModel):
    """
    网盘分享空间表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='分享空间ID')
    title: str | None = Field(default='', description='分享空间名称')
    admin_id: int | None = Field(default=0, description='创建人')
    director_uids: str | None = Field(default='', description='管理人员，逗号分隔')
    group_uids: str | None = Field(default='', description='群组成员，逗号分隔')
    create_time: int | None = Field(default=0, description='创建时间')
    update_time: int | None = Field(default=0, description='更新时间')
    delete_time: int | None = Field(default=0, description='删除时间')

    @Xss(field_name='title', message='分享空间名称不能包含脚本字符')
    @NotBlank(field_name='title', message='分享空间名称不能为空')
    @Size(field_name='title', min_length=0, max_length=255, message='分享空间名称长度不能超过255个字符')
    def get_title(self) -> str | None:
        return self.title

    def validate_fields(self) -> None:
        self.get_title()


class DiskGroupPageQueryModel(DiskGroupModel):
    """
    网盘分享空间分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键字')


class AddDiskGroupModel(DiskGroupModel):
    """
    新增网盘分享空间模型
    """

    pass


class EditDiskGroupModel(AddDiskGroupModel):
    """
    编辑网盘分享空间模型
    """

    id: int = Field(description='分享空间ID')


class DeleteDiskGroupModel(BaseModel):
    """
    删除网盘分享空间模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的分享空间ID')
