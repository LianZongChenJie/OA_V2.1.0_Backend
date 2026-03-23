from datetime import datetime
from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss
from decimal import Decimal

class PropertyRepairModel(BaseModel):
    """
    資產維修記錄表對應 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    property_id: int | None = Field(default=None, description='資產 ID')
    repair_time: int | None = Field(default=None, description='維修日期')
    director_id: int | None = Field(default=None, description='跟進人 ID')
    admin_id: int | None = Field(default=None, description='創建人')
    cost: Decimal | None = Field(default=None, description='維修費用')
    content: str | None = Field(default=None, description='維修原因')
    file_ids: str | None = Field(default=None, description='附件 ids')
    create_time: int | None = Field(default=None, description='創建時間')
    update_time: int | None = Field(default=None, description='更新時間')
    delete_time: int | None = Field(default=None, description='刪除時間')

    # 關聯查詢返回的字段
    property_name: str | None = Field(default=None, description='資產名稱')
    director_name: str | None = Field(default=None, description='跟進人姓名')

    @field_validator('repair_time', mode='before')
    @classmethod
    def validate_repair_time(cls, value: Any) -> int | None:
        """
        验证并转换维修时间字段，支持时间戳和日期字符串
        """
        if value is None:
            return None
        
        # 如果已经是整数（时间戳），直接返回
        if isinstance(value, int):
            return value
        
        # 如果是字符串，尝试解析为日期
        if isinstance(value, str):
            try:
                # 尝试解析日期字符串（如 "2026-03-23"）
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp())
            except ValueError:
                # 如果不是 ISO 格式，尝试直接转换为整数
                try:
                    return int(value)
                except ValueError:
                    pass
        
        return value

    @Xss(field_name='content', message='維修原因不能包含腳本字符')
    @Size(field_name='content', min_length=0, max_length=65535, message='維修原因長度不能超過 65535 個字符')
    def get_content(self) -> str | None:
        return self.content

    def validate_fields(self) -> None:
        self.get_content()

class PropertyRepairQueryModel(PropertyRepairModel):
    """
    資產維修記錄不分頁查詢模型
    """
    pass

class PropertyRepairPageQueryModel(PropertyRepairQueryModel):
    """
    資產維修記錄分頁查詢模型
    """

    page_num: int = Field(default=1, description='當前頁碼')
    page_size: int = Field(default=10, description='每頁記錄數')
    begin_time: str | None = Field(default=None, description='開始時間')
    end_time: str | None = Field(default=None, description='結束時間')
    keywords: str | None = Field(default=None, description='搜索關鍵詞')

class AddPropertyRepairModel(PropertyRepairModel):
    """
    新增資產維修記錄模型
    """
    pass

class EditPropertyRepairModel(AddPropertyRepairModel):
    """
    編輯資產維修記錄模型
    """
    pass

class DeletePropertyRepairModel(BaseModel):
    """
    刪除資產維修記錄模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要刪除的維修記錄 ID')
