from datetime import datetime
from typing import Literal, Any
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size, Xss


class CarModel(BaseModel):
    """
    车辆管理表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    title: str | None = Field(default=None, description='车辆名称')
    name: str | None = Field(default=None, description='车辆牌号')
    oil: str | None = Field(default=None, description='油耗')
    mileage: Decimal | None = Field(default=None, description='开始里程数')
    seats: int | None = Field(default=None, description='座位数')
    color: str | None = Field(default=None, description='车身颜色')
    vin: str | None = Field(default=None, description='车架号')
    engine: str | None = Field(default=None, description='发动机号')
    buy_time: int | None = Field(default=None, description='购买日期')
    price: Decimal | None = Field(default=None, description='购买价格')
    thumb: int | None = Field(default=None, description='车辆照片 ID')
    types: int | None = Field(default=None, description='车辆类型:1 轿车，2 面包车，3 越野车，4 吉普车，5 巴士，6 工具车，7 卡车，8 其他')
    driver: int | None = Field(default=None, description='驾驶员 ID')
    insure_time: int | None = Field(default=None, description='保险到期时间')
    review_time: int | None = Field(default=None, description='年审到期时间')
    file_ids: str | None = Field(default=None, description='附件 ID')
    remark: str | None = Field(default=None, description='备注')
    status: int | None = Field(default=None, description='当前状态:1 可用，2 停用，3 维修，4 报废')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    # 关联查询返回的字段
    driver_name: str | None = Field(default=None, description='驾驶员姓名')

    @field_validator('buy_time', 'insure_time', 'review_time', mode='before')
    @classmethod
    def validate_date_fields(cls, value: Any) -> int | None:
        """
        验证并转换日期字段，支持时间戳和日期字符串
        """
        if value is None:
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp())
            except ValueError:
                try:
                    return int(value)
                except ValueError:
                    pass

        return value

    @Xss(field_name='remark', message='备注不能包含脚本字符')
    @Size(field_name='remark', min_length=0, max_length=1000, message='备注长度不能超过 1000 个字符')
    def get_remark(self) -> str | None:
        return self.remark

    def validate_fields(self) -> None:
        self.get_remark()


class CarQueryModel(CarModel):
    """
    车辆不分页查询模型
    """
    pass


class CarPageQueryModel(CarQueryModel):
    """
    车辆分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词（车辆名称/车牌号码）')


class AddCarModel(CarModel):
    """
    新增车辆模型
    """
    pass


class EditCarModel(AddCarModel):
    """
    编辑车辆模型
    """
    pass


class DeleteCarModel(BaseModel):
    """
    删除车辆模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的车辆 ID')


# ==================== 维修/保养记录相关模型 ====================

class CarRepairModel(BaseModel):
    """
    车辆维修/保养记录表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    car_id: int | None = Field(default=None, description='车辆 ID')
    repair_time: int | None = Field(default=None, description='维修/保养时间')
    types: int | None = Field(default=None, description='类型:1 维修，2 保养')
    amount: Decimal | None = Field(default=None, description='维修/保养金额')
    content: str | None = Field(default=None, description='维修/保养原因&内容')
    address: str | None = Field(default=None, description='维修 (保养) 地点')
    file_ids: str | None = Field(default=None, description='附件 ID')
    handled: int | None = Field(default=None, description='经手人 ID')
    admin_id: int | None = Field(default=None, description='创建人')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    # 关联查询返回的字段
    car_name: str | None = Field(default=None, description='车辆名称')
    handled_name: str | None = Field(default=None, description='处理人姓名')

    @field_validator('repair_time', mode='before')
    @classmethod
    def validate_repair_time(cls, value: Any) -> int | None:
        """
        验证并转换维修时间字段
        """
        if value is None:
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp())
            except ValueError:
                try:
                    return int(value)
                except ValueError:
                    pass

        return value

    @Xss(field_name='content', message='维修/保养原因不能包含脚本字符')
    @Size(field_name='content', min_length=0, max_length=65535, message='长度不能超过 65535 个字符')
    def get_content(self) -> str | None:
        return self.content

    def validate_fields(self) -> None:
        self.get_content()


class CarRepairPageQueryModel(CarRepairModel):
    """
    维修/保养记录分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    diff_time: str | None = Field(default=None, description='时间范围')


class AddCarRepairModel(CarRepairModel):
    """
    新增维修/保养记录模型
    """
    pass


class EditCarRepairModel(AddCarRepairModel):
    """
    编辑维修/保养记录模型
    """
    pass


class DeleteCarRepairModel(BaseModel):
    """
    删除维修/保养记录模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的记录 ID')


# ==================== 费用记录相关模型 ====================

class CarFeeModel(BaseModel):
    """
    车辆费用记录表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    car_id: int | None = Field(default=None, description='车辆 ID')
    title: str | None = Field(default=None, description='费用名称')
    fee_time: int | None = Field(default=None, description='费用时间')
    types: int | None = Field(default=None, description='费用类型')
    amount: Decimal | None = Field(default=None, description='金额')
    file_ids: str | None = Field(default=None, description='附件 ids')
    content: str | None = Field(default=None, description='费用内容')
    handled: int | None = Field(default=None, description='处理人 ID')
    admin_id: int | None = Field(default=None, description='创建人')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    # 关联查询返回的字段
    car_name: str | None = Field(default=None, description='车辆名称')
    handled_name: str | None = Field(default=None, description='处理人姓名')
    types_str: str | None = Field(default=None, description='费用类型名称')

    @field_validator('fee_time', mode='before')
    @classmethod
    def validate_fee_time(cls, value: Any) -> int | None:
        """
        验证并转换费用时间字段
        """
        if value is None:
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp())
            except ValueError:
                try:
                    return int(value)
                except ValueError:
                    pass

        return value

    @Xss(field_name='title', message='费用名称不能包含脚本字符')
    @NotBlank(field_name='title', message='费用名称不能为空')
    def get_title(self) -> str | None:
        return self.title

    def validate_fields(self) -> None:
        self.get_title()


class CarFeePageQueryModel(CarFeeModel):
    """
    费用记录分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
    keywords: str | None = Field(default=None, description='搜索关键词')
    diff_time: str | None = Field(default=None, description='时间范围')
    types: int | None = Field(default=None, description='费用类型')


class AddCarFeeModel(CarFeeModel):
    """
    新增费用记录模型
    """
    pass


class EditCarFeeModel(AddCarFeeModel):
    """
    编辑费用记录模型
    """
    pass


class DeleteCarFeeModel(BaseModel):
    """
    删除费用记录模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的费用记录 ID')


# ==================== 里程记录相关模型 ====================

class CarMileageModel(BaseModel):
    """
    车辆里程记录表对应 pydantic 模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='ID')
    car_id: int | None = Field(default=None, description='车辆 ID')
    mileage: Decimal | None = Field(default=None, description='里程数')
    mileage_time: int | None = Field(default=None, description='里程时间')
    admin_id: int | None = Field(default=None, description='记录人 ID')
    create_time: int | None = Field(default=None, description='创建时间')
    update_time: int | None = Field(default=None, description='更新时间')
    delete_time: int | None = Field(default=None, description='删除时间')

    @field_validator('mileage_time', mode='before')
    @classmethod
    def validate_mileage_time(cls, value: Any) -> int | None:
        """
        验证并转换里程时间字段
        """
        if value is None:
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
                return int(dt.timestamp())
            except ValueError:
                try:
                    return int(value)
                except ValueError:
                    pass

        return value


class CarMileagePageQueryModel(CarMileageModel):
    """
    里程记录分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddCarMileageModel(CarMileageModel):
    """
    新增里程记录模型
    """
    pass


class EditCarMileageModel(AddCarMileageModel):
    """
    编辑里程记录模型
    """
    pass


class DeleteCarMileageModel(BaseModel):
    """
    删除里程记录模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: int = Field(description='需要删除的里程记录 ID')
