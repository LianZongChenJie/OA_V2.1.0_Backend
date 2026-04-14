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
            if key.endswith('Time') and value is not None and isinstance(value, int):
                item_dict[key] = format_timestamp(value)
        return item_dict

    @staticmethod
    def list_time_format(list_dict: List[Dict]) -> List[Dict]:
        """批量时间格式化"""
        return [ModelConverter.time_format(item) for item in list_dict]

    @classmethod
    def transform_rows(cls, rows: List[dict]) -> List[dict]:
        """转换行数据（驼峰 + 时间格式化）"""
        if not rows:
            return []

        result = []
        for row in rows:
            transformed = {}
            for key, value in row.items():
                # 驼峰转换
                camel_key = cls._to_camel(key)
                # 时间格式化
                if key in ['create_time', 'update_time', 'check_time', 'start_time', 'end_time', 'pay_time']:
                    value = format_timestamp(value)
                transformed[camel_key] = value
            result.append(transformed)

        return result

    @staticmethod
    def _to_camel(snake_str: str) -> str:
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])


class ResponseConverter:
    """响应数据转换器"""

    # 需要格式化的时间字段
    TIME_FIELDS = []

    @classmethod
    def convert_row(cls, row: dict, table_name: str) -> dict:
        """转换单行数据"""
        result = {}

        for key, value in row.items():
            camel_key = to_camel(key)

            # 处理 OaDepartmentChange 实体
            if key == table_name and hasattr(value, '__table__'):
                # 将实体转换为字典
                entity_dict = {}
                for col in value.__table__.columns:
                    col_value = getattr(value, col.name)
                    # 格式化时间
                    if col.name in cls.TIME_FIELDS and isinstance(col_value, int):
                        col_value = format_timestamp(col_value)
                    entity_dict[to_camel(col.name)] = col_value
                result[table_name] = entity_dict

            # 处理嵌套字典
            elif isinstance(value, dict):
                result[camel_key] = cls.convert_row(value, table_name)

            # 处理列表
            elif isinstance(value, list):
                result[camel_key] = [
                    cls.convert_row(item, table_name) if isinstance(item, dict) else item
                    for item in value
                ]

            # 格式化时间字段
            elif key in cls.TIME_FIELDS and isinstance(value, int):
                result[camel_key] = format_timestamp(value)

            else:
                result[camel_key] = value

        return result

    @classmethod
    def convert_page_result(cls, page_result, time_fields:list, table_name:str):
        """转换分页结果"""
        cls.TIME_FIELDS = time_fields
        if hasattr(page_result, 'rows') and page_result.rows:
            page_result.rows = [cls.convert_row(dict(row),table_name) for row in page_result.rows]
        for row in page_result.rows:
            row.update(row[table_name])
            row.pop(table_name)
        return page_result

    @classmethod
    def convert_to_camel_and_format_time(cls, data: dict, time_fields:list) -> dict:
        """将字典的键转换为驼峰并格式化时间字段"""

        result = {}
        for key, value in data.items():
            # 转换为驼峰
            camel_key = to_camel(key)

            # 格式化时间字段
            if key in time_fields and isinstance(value, int):
                value = format_timestamp(value)

            result[camel_key] = value

        return result

    @classmethod
    def convert_to_camel_and_format_time_list(cls, datas: List[dict], time_fields:list) -> List[dict]:
        """将字典的键转换为驼峰并格式化时间字段"""
        result = []
        for data in datas:
            if data is None:
                continue

            map = {}

            # 处理字典
            if isinstance(data, dict):
                items = data.items()
            # 处理 SQLAlchemy 实体对象
            elif hasattr(data, '__table__'):
                # 获取实体的所有列
                for column in data.__table__.columns:
                    key = column.name
                    value = getattr(data, key)
                    items = [(key, value)]
                    # 需要遍历每个字段
                    for key, value in [(col.name, getattr(data, col.name)) for col in data.__table__.columns]:
                        camel_key = to_camel(key)
                        if key in time_fields and isinstance(value, int):
                            value = format_timestamp(value)
                        map[camel_key] = value
                    result.append(map)
                    continue
            # 处理普通对象（有 __dict__）
            elif hasattr(data, '__dict__'):
                items = data.__dict__.items()
            else:
                continue

            # 处理字典类型的 items
            if isinstance(data, dict) or (not hasattr(data, '__table__')):
                for key, value in items:
                    if key.startswith('_'):
                        continue
                    camel_key = to_camel(key)
                    if key in time_fields and isinstance(value, int):
                        value = format_timestamp(value)
                    map[camel_key] = value
                result.append(map)

        return result
