# module_dashboard/entity/vo/dashboard_vo.py
from pydantic import BaseModel, ConfigDict, Field


class UrgentItemModel(BaseModel):
    """紧急事项项模型"""
    model_config = ConfigDict(populate_by_name=True)
    
    name: str | None = Field(default=None, description='事项名称')
    num: int = Field(default=0, description='数量')
    target_name: str | None = Field(default=None, alias='targetName', description='目标名称')
    target_path: str | None = Field(default=None, alias='targetPath', description='目标路径')
