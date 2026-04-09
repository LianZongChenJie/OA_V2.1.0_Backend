"""
网盘文件相关 Pydantic 模型
"""
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class DiskModel(BaseModel):
    """
    网盘文件表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: int | None = Field(default=None, description='文件ID')
    pid: int | None = Field(default=0, description='所在文件夹目录ID')
    did: int | None = Field(default=0, description='所属部门')
    types: int | None = Field(default=0, description='类型:0文件,1在线文档,2文件夹')
    action_id: int | None = Field(default=0, description='相关联id')
    group_id: int | None = Field(default=0, description='分享空间id')
    name: str | None = Field(default='', description='文件名称')
    file_ext: str | None = Field(default='', description='文件后缀名称')
    file_size: int | None = Field(default=0, description='文件大小')
    is_star: int | None = Field(default=0, description='是否标星')
    admin_id: int | None = Field(default=0, description='创建人')
    create_time: int | None = Field(default=0, description='创建时间')
    update_time: int | None = Field(default=0, description='修改时间')
    delete_time: int | None = Field(default=0, description='删除时间')
    clear_time: int | None = Field(default=0, description='清除时间')

    @Xss(field_name='name', message='文件名称不能包含脚本字符')
    @NotBlank(field_name='name', message='文件名称不能为空')
    @Size(field_name='name', min_length=0, max_length=200, message='文件名称长度不能超过200个字符')
    def get_name(self) -> str | None:
        return self.name

    def validate_fields(self) -> None:
        self.get_name()


class DiskPageQueryModel(DiskModel):
    """
    网盘文件分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键字')
    ext: str | None = Field(default=None, description='文件扩展名筛选，逗号分隔')


class AddDiskModel(DiskModel):
    """
    新增网盘文件模型
    """

    pass


class EditDiskModel(AddDiskModel):
    """
    编辑网盘文件模型
    """

    id: int = Field(description='文件ID')


class DeleteDiskModel(BaseModel):
    """
    删除网盘文件模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的文件ID列表，逗号分隔')


class MoveDiskModel(BaseModel):
    """
    移动网盘文件模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要移动的文件ID列表，逗号分隔')
    pid: int = Field(description='目标文件夹ID')


class StarDiskModel(BaseModel):
    """
    标星网盘文件模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要标星的文件ID列表，逗号分隔')


class UnstarDiskModel(BaseModel):
    """
    取消标星网盘文件模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要取消标星的文件ID列表，逗号分隔')


class BackDiskModel(BaseModel):
    """
    恢复网盘文件模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要恢复的文件ID列表，逗号分隔')


class ClearDiskModel(BaseModel):
    """
    清除网盘文件模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要清除的文件ID列表，逗号分隔')
