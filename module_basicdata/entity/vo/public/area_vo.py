from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel

class AreaBaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(None, description='ID')
    pid: int | None = Field(None, description='父级ID')
    name: str | None = Field(None, description='名称')
    shortname: str | None = Field(None, description='简称')
    longitude: str | None = Field(None, description='经度')
    latitude: str | None = Field(None, description='纬度')
    level: int | None = Field(None, description='级别：1省/直辖市 2市 3区/县')
    sort: int | None = Field(None, description='排序')
    status: int | None = Field(None, description='状态:默认1有效')

class AreaTreeModel(AreaBaseModel):
    """
    树模型
    """

    model_config = ConfigDict(alias_generator=to_camel)
    children: list['AreaTreeModel'] | None = Field(default=None, description='子树')