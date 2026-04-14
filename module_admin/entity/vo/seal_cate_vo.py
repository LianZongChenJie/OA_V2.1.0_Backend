from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class SealCateModel(BaseModel):
    """
    印章类别表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='印章类别 ID')
    title: str | None = Field(default=None, description='印章名称')
    dids: str | None = Field(default=None, description='应用部门')
    keep_uid: int | None = Field(default=None, description='保管人')
    status: Literal[-1, 0, 1] | None = Field(default=None, description='状态：-1 删除 0 禁用 1 启用')
    remark: str | None = Field(default=None, description='用途简述')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')

    # 扩展字段，用于列表展示
    dept_names: list[str] | None = Field(default=None, description='应用部门名称列表')
    keeper_name: str | None = Field(default=None, description='保管人姓名')

    @Xss(field_name='title', message='印章名称不能包含脚本字符')
    @NotBlank(field_name='title', message='印章名称不能为空')
    @Size(field_name='title', min_length=0, max_length=100, message='印章名称长度不能超过 100 个字符')
    def get_title(self) -> str | None:
        return self.title

    @Size(field_name='dids', min_length=0, max_length=255, message='应用部门长度不能超过 255 个字符')
    def get_dids(self) -> str | None:
        return self.dids

    @Size(field_name='remark', min_length=0, max_length=1000, message='用途简述长度不能超过 1000 个字符')
    def get_remark(self) -> str | None:
        return self.remark

    def validate_fields(self) -> None:
        self.get_title()
        self.get_dids()
        self.get_remark()


class SealCatePageQueryModel(SealCateModel):
    """
    印章类别管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddSealCateModel(SealCateModel):
    """
    新增印章类别模型
    """

    pass


class EditSealCateModel(AddSealCateModel):
    """
    编辑印章类别模型
    """

    pass


class DeleteSealCateModel(BaseModel):
    """
    删除印章类别模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的印章类别 ID')

