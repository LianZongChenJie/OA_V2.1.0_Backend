from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.car_dao import CarDao, CarRepairDao, CarFeeDao, CarMileageDao
from module_admin.entity.vo.car_vo import (
    AddCarModel,
    DeleteCarModel,
    EditCarModel,
    CarPageQueryModel,
    CarRepairPageQueryModel,
    AddCarRepairModel,
    EditCarRepairModel,
    DeleteCarRepairModel,
    CarFeePageQueryModel,
    AddCarFeeModel,
    EditCarFeeModel,
    DeleteCarFeeModel,
    CarMileagePageQueryModel,
    AddCarMileageModel,
    EditCarMileageModel,
    DeleteCarMileageModel,
)
from utils.camel_converter import ModelConverter
from utils.common_util import CamelCaseUtil


class CarService:
    """
    车辆管理服务层
    """

    @classmethod
    async def get_car_list_services(
            cls, query_db: AsyncSession, query_object: CarPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取车辆列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 车辆列表信息对象
        """
        car_list_result = await CarDao.get_car_list(query_db, query_object, is_page)
        
        # 如果返回的是分页结果，需要转换 rows 中的数据
        if hasattr(car_list_result, 'rows'):
            transformed_rows = []
            for row in car_list_result.rows:
                # row 是一个元组 (OaCar, driver_name)
                if isinstance(row, (list, tuple)):
                    car_obj = row[0]
                    extra_fields = {
                        'driverName': row[1] if len(row) > 1 else None,
                    }
                    
                    # 将 ORM 对象转换为字典（已经是驼峰命名）
                    car_dict = CamelCaseUtil.transform_result(car_obj)
                    # 合并扩展字段
                    car_dict.update(extra_fields)
                    # 格式化时间字段
                    car_dict = ModelConverter.time_format(car_dict)
                    transformed_rows.append(car_dict)
                else:
                    transformed_dict = CamelCaseUtil.transform_result(row)
                    transformed_dict = ModelConverter.time_format(transformed_dict)
                    transformed_rows.append(transformed_dict)
            
            car_list_result.rows = transformed_rows

        return car_list_result

    @classmethod
    async def add_car_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddCarModel
    ) -> CrudResponseModel:
        """
        新增车辆信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增车辆对象
        :return: 新增车辆校验结果
        """
        try:
            current_time = int(datetime.now().timestamp())
            car_data = page_object.model_dump(exclude_unset=True)
            car_data['create_time'] = current_time
            car_data['update_time'] = current_time
            car_data['delete_time'] = 0

            # 处理金额字段，确保转换为 float
            if 'price' in car_data and car_data['price'] is not None:
                if isinstance(car_data['price'], Decimal):
                    car_data['price'] = float(car_data['price'])

            if 'mileage' in car_data and car_data['mileage'] is not None:
                if isinstance(car_data['mileage'], Decimal):
                    car_data['mileage'] = float(car_data['mileage'])

            await CarDao.add_car_dao(query_db, car_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_car_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCarModel
    ) -> CrudResponseModel:
        """
        编辑车辆信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑车辆对象
        :return: 编辑车辆校验结果
        """
        car_data = page_object.model_dump(exclude_unset=True)
        car_info = await cls.car_detail_services(query_db, page_object.id)

        if car_info.id:
            try:
                car_data['update_time'] = int(datetime.now().timestamp())

                # 处理金额字段
                if 'price' in car_data and car_data['price'] is not None:
                    if isinstance(car_data['price'], Decimal):
                        car_data['price'] = float(car_data['price'])

                if 'mileage' in car_data and car_data['mileage'] is not None:
                    if isinstance(car_data['mileage'], Decimal):
                        car_data['mileage'] = float(car_data['mileage'])

                await CarDao.edit_car_dao(query_db, car_data)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='车辆不存在')

    @classmethod
    async def delete_car_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteCarModel
    ) -> CrudResponseModel:
        """
        删除车辆信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除车辆对象
        :return: 删除车辆校验结果
        """
        if page_object.id:
            try:
                car = await cls.car_detail_services(query_db, page_object.id)
                if not car.id:
                    raise ServiceException(message='车辆不存在')

                await CarDao.delete_car_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入车辆 id 为空')

    @classmethod
    async def car_detail_services(cls, query_db: AsyncSession, car_id: int) -> CarPageQueryModel:
        """
        获取车辆详细信息 service

        :param query_db: orm 对象
        :param car_id: 车辆 ID
        :return: 车辆 ID 对应的信息
        """
        car = await CarDao.get_car_detail_by_id(query_db, car_id)
        result = CarPageQueryModel(**CamelCaseUtil.transform_result(car)) if car else CarPageQueryModel()

        return result


class CarRepairService:
    """
    车辆维修/保养记录服务层
    """

    @classmethod
    async def get_car_repair_list_services(
            cls, query_db: AsyncSession, query_object: CarRepairPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取维修/保养记录列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 维修/保养记录列表信息对象
        """
        repair_list_result = await CarRepairDao.get_car_repair_list(query_db, query_object, is_page)
        
        # 如果返回的是分页结果，需要转换 rows 中的数据
        if hasattr(repair_list_result, 'rows'):
            transformed_rows = []
            for row in repair_list_result.rows:
                # row 是一个元组 (OaCarRepair, car_name, handled_name)
                if isinstance(row, (list, tuple)):
                    repair_obj = row[0]
                    extra_fields = {
                        'carName': row[1] if len(row) > 1 else None,
                        'handledName': row[2] if len(row) > 2 else None,
                    }
                    
                    # 将 ORM 对象转换为字典（已经是驼峰命名）
                    repair_dict = CamelCaseUtil.transform_result(repair_obj)
                    # 合并扩展字段
                    repair_dict.update(extra_fields)
                    # 格式化时间字段
                    repair_dict = ModelConverter.time_format(repair_dict)
                    transformed_rows.append(repair_dict)
                else:
                    transformed_dict = CamelCaseUtil.transform_result(row)
                    transformed_dict = ModelConverter.time_format(transformed_dict)
                    transformed_rows.append(transformed_dict)
            
            repair_list_result.rows = transformed_rows

        return repair_list_result

    @classmethod
    async def add_car_repair_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddCarRepairModel
    ) -> CrudResponseModel:
        """
        新增维修/保养记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增维修/保养记录对象
        :return: 新增维修/保养记录校验结果
        """
        try:
            current_time = int(datetime.now().timestamp())
            repair_data = page_object.model_dump(exclude_unset=True)
            repair_data['create_time'] = current_time
            repair_data['update_time'] = current_time
            repair_data['delete_time'] = 0

            # 如果未传入维修时间，使用当前时间
            if 'repair_time' not in repair_data or repair_data['repair_time'] is None:
                repair_data['repair_time'] = current_time

            # 处理金额字段
            if 'amount' in repair_data and repair_data['amount'] is not None:
                if isinstance(repair_data['amount'], Decimal):
                    repair_data['amount'] = float(repair_data['amount'])

            await CarRepairDao.add_car_repair_dao(query_db, repair_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_car_repair_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCarRepairModel
    ) -> CrudResponseModel:
        """
        编辑维修/保养记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑维修/保养记录对象
        :return: 编辑维修/保养记录校验结果
        """
        repair_data = page_object.model_dump(exclude_unset=True)
        repair_info = await cls.car_repair_detail_services(query_db, page_object.id)

        if repair_info.id:
            try:
                repair_data['update_time'] = int(datetime.now().timestamp())

                # 处理金额字段
                if 'amount' in repair_data and repair_data['amount'] is not None:
                    if isinstance(repair_data['amount'], Decimal):
                        repair_data['amount'] = float(repair_data['amount'])

                await CarRepairDao.edit_car_repair_dao(query_db, repair_data)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='维修/保养记录不存在')

    @classmethod
    async def delete_car_repair_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteCarRepairModel
    ) -> CrudResponseModel:
        """
        删除维修/保养记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除维修/保养记录对象
        :return: 删除维修/保养记录校验结果
        """
        if page_object.id:
            try:
                repair = await cls.car_repair_detail_services(query_db, page_object.id)
                if not repair.id:
                    raise ServiceException(message='记录不存在')

                await CarRepairDao.delete_car_repair_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入记录 id 为空')

    @classmethod
    async def car_repair_detail_services(cls, query_db: AsyncSession, repair_id: int) -> CarRepairPageQueryModel:
        """
        获取维修/保养记录详细信息 service

        :param query_db: orm 对象
        :param repair_id: 记录 ID
        :return: 记录 ID 对应的信息
        """
        repair = await CarRepairDao.get_car_repair_detail_by_id(query_db, repair_id)
        result = CarRepairPageQueryModel(**CamelCaseUtil.transform_result(repair)) if repair else CarRepairPageQueryModel()

        return result


class CarFeeService:
    """
    车辆费用记录服务层
    """

    @classmethod
    async def get_car_fee_list_services(
            cls, query_db: AsyncSession, query_object: CarFeePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取费用记录列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 费用记录列表信息对象
        """
        fee_list_result = await CarFeeDao.get_car_fee_list(query_db, query_object, is_page)
        
        # 如果返回的是分页结果，需要转换 rows 中的数据
        if hasattr(fee_list_result, 'rows'):
            transformed_rows = []
            for row in fee_list_result.rows:
                # row 是一个元组 (OaCarFee, car_name, handled_name, types_str)
                if isinstance(row, (list, tuple)):
                    fee_obj = row[0]
                    extra_fields = {
                        'carName': row[1] if len(row) > 1 else None,
                        'handledName': row[2] if len(row) > 2 else None,
                        'typesStr': row[3] if len(row) > 3 else None,
                    }
                    
                    # 将 ORM 对象转换为字典（已经是驼峰命名）
                    fee_dict = CamelCaseUtil.transform_result(fee_obj)
                    # 合并扩展字段
                    fee_dict.update(extra_fields)
                    # 格式化时间字段
                    fee_dict = ModelConverter.time_format(fee_dict)
                    transformed_rows.append(fee_dict)
                else:
                    transformed_dict = CamelCaseUtil.transform_result(row)
                    transformed_dict = ModelConverter.time_format(transformed_dict)
                    transformed_rows.append(transformed_dict)
            
            fee_list_result.rows = transformed_rows

        return fee_list_result

    @classmethod
    async def add_car_fee_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddCarFeeModel
    ) -> CrudResponseModel:
        """
        新增费用记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增费用记录对象
        :return: 新增费用记录校验结果
        """
        try:
            current_time = int(datetime.now().timestamp())
            fee_data = page_object.model_dump(exclude_unset=True)
            fee_data['create_time'] = current_time
            fee_data['update_time'] = current_time
            fee_data['delete_time'] = 0

            # 如果未传入费用时间，使用当前时间
            if 'fee_time' not in fee_data or fee_data['fee_time'] is None:
                fee_data['fee_time'] = current_time

            # 处理金额字段
            if 'amount' in fee_data and fee_data['amount'] is not None:
                if isinstance(fee_data['amount'], Decimal):
                    fee_data['amount'] = float(fee_data['amount'])

            await CarFeeDao.add_car_fee_dao(query_db, fee_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_car_fee_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCarFeeModel
    ) -> CrudResponseModel:
        """
        编辑费用记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑费用记录对象
        :return: 编辑费用记录校验结果
        """
        fee_data = page_object.model_dump(exclude_unset=True)
        fee_info = await cls.car_fee_detail_services(query_db, page_object.id)

        if fee_info.id:
            try:
                fee_data['update_time'] = int(datetime.now().timestamp())

                # 处理金额字段
                if 'amount' in fee_data and fee_data['amount'] is not None:
                    if isinstance(fee_data['amount'], Decimal):
                        fee_data['amount'] = float(fee_data['amount'])

                await CarFeeDao.edit_car_fee_dao(query_db, fee_data)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='费用记录不存在')

    @classmethod
    async def delete_car_fee_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteCarFeeModel
    ) -> CrudResponseModel:
        """
        删除费用记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除费用记录对象
        :return: 删除费用记录校验结果
        """
        if page_object.id:
            try:
                fee = await cls.car_fee_detail_services(query_db, page_object.id)
                if not fee.id:
                    raise ServiceException(message='费用记录不存在')

                await CarFeeDao.delete_car_fee_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入费用记录 id 为空')

    @classmethod
    async def car_fee_detail_services(cls, query_db: AsyncSession, fee_id: int) -> CarFeePageQueryModel:
        """
        获取费用记录详细信息 service

        :param query_db: orm 对象
        :param fee_id: 费用 ID
        :return: 费用 ID 对应的信息
        """
        fee = await CarFeeDao.get_car_fee_detail_by_id(query_db, fee_id)
        result = CarFeePageQueryModel(**CamelCaseUtil.transform_result(fee)) if fee else CarFeePageQueryModel()

        return result


class CarMileageService:
    """
    车辆里程记录服务层
    """

    @classmethod
    async def get_car_mileage_list_services(
            cls, query_db: AsyncSession, query_object: CarMileagePageQueryModel, car_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取里程记录列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param car_id: 车辆 ID
        :param is_page: 是否开启分页
        :return: 里程记录列表信息对象
        """
        mileage_list_result = await CarMileageDao.get_car_mileage_list(query_db, query_object, car_id, is_page)
        
        # 如果返回的是分页结果，需要转换 rows 中的数据
        if hasattr(mileage_list_result, 'rows'):
            transformed_rows = []
            for row in mileage_list_result.rows:
                transformed_dict = CamelCaseUtil.transform_result(row)
                transformed_dict = ModelConverter.time_format(transformed_dict)
                transformed_rows.append(transformed_dict)
            
            mileage_list_result.rows = transformed_rows

        return mileage_list_result

    @classmethod
    async def add_car_mileage_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddCarMileageModel
    ) -> CrudResponseModel:
        """
        新增里程记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增里程记录对象
        :return: 新增里程记录校验结果
        """
        try:
            current_time = int(datetime.now().timestamp())
            mileage_data = page_object.model_dump(exclude_unset=True)
            mileage_data['create_time'] = current_time
            mileage_data['update_time'] = current_time
            mileage_data['delete_time'] = 0

            # 如果未传入里程时间，使用当前时间
            if 'mileage_time' not in mileage_data or mileage_data['mileage_time'] is None:
                mileage_data['mileage_time'] = current_time

            # 处理里程字段
            if 'mileage' in mileage_data and mileage_data['mileage'] is not None:
                if isinstance(mileage_data['mileage'], Decimal):
                    mileage_data['mileage'] = float(mileage_data['mileage'])

            await CarMileageDao.add_car_mileage_dao(query_db, mileage_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_car_mileage_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCarMileageModel
    ) -> CrudResponseModel:
        """
        编辑里程记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑里程记录对象
        :return: 编辑里程记录校验结果
        """
        mileage_data = page_object.model_dump(exclude_unset=True)
        mileage_info = await cls.car_mileage_detail_services(query_db, page_object.id)

        if mileage_info.id:
            try:
                mileage_data['update_time'] = int(datetime.now().timestamp())

                # 处理里程字段
                if 'mileage' in mileage_data and mileage_data['mileage'] is not None:
                    if isinstance(mileage_data['mileage'], Decimal):
                        mileage_data['mileage'] = float(mileage_data['mileage'])

                await CarMileageDao.edit_car_mileage_dao(query_db, mileage_data)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='里程记录不存在')

    @classmethod
    async def delete_car_mileage_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteCarMileageModel
    ) -> CrudResponseModel:
        """
        删除里程记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除里程记录对象
        :return: 删除里程记录校验结果
        """
        if page_object.id:
            try:
                mileage = await cls.car_mileage_detail_services(query_db, page_object.id)
                if not mileage.id:
                    raise ServiceException(message='里程记录不存在')

                await CarMileageDao.delete_car_mileage_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入里程记录 id 为空')

    @classmethod
    async def car_mileage_detail_services(cls, query_db: AsyncSession, mileage_id: int) -> CarMileagePageQueryModel:
        """
        获取里程记录详细信息 service

        :param query_db: orm 对象
        :param mileage_id: 里程 ID
        :return: 里程 ID 对应的信息
        """
        mileage = await CarMileageDao.get_car_mileage_detail_by_id(query_db, mileage_id)
        result = CarMileagePageQueryModel(**CamelCaseUtil.transform_result(mileage)) if mileage else CarMileagePageQueryModel()

        return result

    @classmethod
    async def get_latest_mileage_services(cls, query_db: AsyncSession, car_id: int) -> float:
        """
        获取车辆最新里程数 service

        :param query_db: orm 对象
        :param car_id: 车辆 ID
        :return: 最新里程数
        """
        latest_mileage = await CarMileageDao.get_latest_mileage(query_db, car_id)

        # 如果数据库中没有里程记录，返回车辆的初始里程
        if latest_mileage is None:
            car = await CarDao.get_car_detail_by_id(query_db, car_id)
            if car and car.mileage:
                latest_mileage = float(car.mileage)
            else:
                latest_mileage = 0.0

        return latest_mileage
