from typing import TypeVar, Type, List, Dict, Any
from pydantic import BaseModel
from pydantic.alias_generators import to_camel
from utils.timeformat import format_timestamp

T = TypeVar('T', bound=BaseModel)
M = TypeVar('M')  # SQLAlchemy 模型

class ModelConverter:
    """模型转换器"""
    
    @staticmethod
    def to_vo(model_obj, vo_class: Type[T]) -> T:
        """
        将 SQLAlchemy 模型转换为 Pydantic VO
        
        Args:
            model_obj: SQLAlchemy 模型实例
            vo_class: Pydantic VO 类
        
        Returns:
            Pydantic VO 实例
        """
        if model_obj is None:
            return None
        
        return vo_class.model_validate(model_obj)
    
    @staticmethod
    def to_vo_list(model_objs: List, vo_class: Type[T]) -> List[T]:
        """批量转换"""
        return [ModelConverter.to_vo(obj, vo_class) for obj in model_objs if obj]
    
    @staticmethod
    def to_dict(model_obj, by_alias: bool = True) -> Dict[str, Any]:
        """
        转换为字典（带驼峰转换）
        
        Args:
            model_obj: SQLAlchemy 模型实例
            by_alias: 是否使用驼峰别名
        
        Returns:
            字典数据
        """
        if model_obj is None:
            return {}
        
        # 获取所有列
        data = {}
        for col in model_obj.__table__.columns:
            value = getattr(model_obj, col.name)
            if by_alias:
                key = to_camel(col.name)
            else:
                key = col.name
            data[key] = value
        
        return data

    @staticmethod
    def to_dict_list(model_objs: List, by_alias: bool = True) -> List[Dict]:
        """批量转换为字典"""
        return [ModelConverter.to_dict(obj, by_alias) for obj in model_objs]

    @staticmethod
    def time_format(item_dict: Dict) -> Dict:
        """时间格式化"""
        for key, value in item_dict.items():
            if key.endswith('Time') and value is not None:
                item_dict[key] = format_timestamp(value)
        return item_dict