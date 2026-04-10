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
from utils.camel_converter import ModelConverter
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
        
        # 如果返回的是分页结果，需要转换 rows 中的数据
        if hasattr(repair_list_result, 'rows'):
            transformed_rows = []
            for row in repair_list_result.rows:
                # row 是一个元组 (OaPropertyRepair, property_name, cate_name, brand_name, director_name)
                if isinstance(row, (list, tuple)):
                    repair_obj = row[0]
                    extra_fields = {
                        'propertyName': row[1] if len(row) > 1 else None,
                        'cateName': row[2] if len(row) > 2 else None,
                        'brandName': row[3] if len(row) > 3 else None,
                        'directorName': row[4] if len(row) > 4 else None,
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
        from module_admin.entity.do.property_repair_do import OaPropertyRepair
        from module_admin.entity.do.property_do import OaProperty
        from module_admin.entity.do.property_cate_do import SysPropertyCate
        from module_admin.entity.do.property_brand_do import SysPropertyBrand
        from module_admin.entity.do.user_do import SysUser
        from sqlalchemy import select
        
        # 连表查询获取关联字段
        query = (
            select(
                OaPropertyRepair,
                OaProperty.title.label('property_name'),
                SysPropertyCate.title.label('cate_name'),
                SysPropertyBrand.title.label('brand_name'),
                SysUser.nick_name.label('director_name')
            )
            .outerjoin(OaProperty, OaPropertyRepair.property_id == OaProperty.id)
            .outerjoin(SysPropertyCate, OaProperty.cate_id == SysPropertyCate.id)
            .outerjoin(SysPropertyBrand, OaProperty.brand_id == SysPropertyBrand.id)
            .outerjoin(SysUser, OaPropertyRepair.director_id == SysUser.user_id)
            .where(OaPropertyRepair.id == repair_id)
        )
        
        result = (await query_db.execute(query)).first()
        
        if result:
            repair_obj = result[0]
            extra_fields = {
                'propertyName': result[1] if len(result) > 1 else None,
                'cateName': result[2] if len(result) > 2 else None,
                'brandName': result[3] if len(result) > 3 else None,
                'directorName': result[4] if len(result) > 4 else None,
            }
            
            # 将 ORM 对象转换为字典
            repair_dict = CamelCaseUtil.transform_result(repair_obj)
            # 合并扩展字段
            repair_dict.update(extra_fields)
            # 格式化时间字段
            repair_dict = ModelConverter.time_format(repair_dict)
            
            return PropertyRepairModel(**repair_dict)
        else:
            raise ServiceException(message=f'維修記錄 ID {repair_id} 不存在')
