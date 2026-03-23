from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.property_repair_dao import PropertyRepairDao
from module_admin.entity.vo.property_repair_vo import (
    AddPropertyRepairModel,
    DeletePropertyRepairModel,
    EditPropertyRepairModel,
    PropertyRepairModel,
    PropertyRepairPageQueryModel,
)
from utils.common_util import CamelCaseUtil

class PropertyRepairService:
    """
    資產維修記錄管理服務層
    """

    @classmethod
    async def get_property_repair_list_services(
            cls, query_db: AsyncSession, query_object: PropertyRepairPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        獲取維修記錄列表信息 service

        :param query_db: orm 對象
        :param query_object: 查詢參數對象
        :param is_page: 是否開啟分頁
        :return: 維修記錄列表信息對象
        """
        repair_list_result = await PropertyRepairDao.get_property_repair_list(query_db, query_object, is_page)

        return CamelCaseUtil.transform_result(repair_list_result)

    @classmethod
    async def add_property_repair_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddPropertyRepairModel
    ) -> CrudResponseModel:
        """
        新增維修記錄信息 service

        :param request: Request 對象
        :param query_db: orm 對象
        :param page_object: 新增維修記錄對象
        :return: 新增維修記錄校驗結果
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

            # 處理金額字段，確保轉換為 float
            if 'cost' in repair_data and repair_data['cost'] is not None:
                if isinstance(repair_data['cost'], Decimal):
                    repair_data['cost'] = float(repair_data['cost'])

            await PropertyRepairDao.add_property_repair_dao(query_db, repair_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_property_repair_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPropertyRepairModel
    ) -> CrudResponseModel:
        """
        編輯維修記錄信息 service

        :param request: Request 對象
        :param query_db: orm 對象
        :param page_object: 編輯維修記錄對象
        :return: 編輯維修記錄校驗結果
        """
        repair_data = page_object.model_dump(exclude_unset=True)
        repair_info = await cls.property_repair_detail_services(query_db, page_object.id)

        if repair_info.id:
            try:
                repair_data['update_time'] = int(datetime.now().timestamp())

                # 處理金額字段
                if 'cost' in repair_data and repair_data['cost'] is not None:
                    if isinstance(repair_data['cost'], Decimal):
                        repair_data['cost'] = float(repair_data['cost'])

                await PropertyRepairDao.edit_property_repair_dao(query_db, repair_data)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='維修記錄不存在')

    @classmethod
    async def delete_property_repair_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeletePropertyRepairModel
    ) -> CrudResponseModel:
        """
        刪除維修記錄信息 service

        :param request: Request 對象
        :param query_db: orm 對象
        :param page_object: 刪除維修記錄對象
        :return: 刪除維修記錄校驗結果
        """
        if page_object.id:
            try:
                repair = await cls.property_repair_detail_services(query_db, page_object.id)
                if not repair.id:
                    raise ServiceException(message='維修記錄不存在')

                await PropertyRepairDao.delete_property_repair_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='刪除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='傳入維修記錄 id 為空')

    @classmethod
    async def property_repair_detail_services(cls, query_db: AsyncSession, repair_id: int) -> PropertyRepairModel:
        """
        獲取維修記錄詳細信息 service

        :param query_db: orm 對象
        :param repair_id: 維修記錄 ID
        :return: 維修記錄 ID 對應的信息
        """
        repair = await PropertyRepairDao.get_property_repair_detail_by_id(query_db, repair_id)
        result = PropertyRepairModel(**CamelCaseUtil.transform_result(repair)) if repair else PropertyRepairModel()

        return result
