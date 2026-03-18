from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.property_unit_dao import PropertyUnitDao
from module_admin.entity.vo.property_unit_vo import (
    AddPropertyUnitModel,
    DeletePropertyUnitModel,
    EditPropertyUnitModel,
    PropertyUnitModel,
    PropertyUnitPageQueryModel,
)
from utils.common_util import CamelCaseUtil


class PropertyUnitService:
    """
    资产单位管理服务层
    """

    @classmethod
    async def get_property_unit_list_services(
            cls, query_db: AsyncSession, query_object: PropertyUnitPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取资产单位列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 资产单位列表信息对象
        """
        property_unit_list_result = await PropertyUnitDao.get_property_unit_list(query_db, query_object, is_page)

        return property_unit_list_result

    @classmethod
    async def get_all_property_unit_list_services(cls, query_db: AsyncSession) -> list[dict[str, Any]]:
        """
        获取所有资产单位列表信息 service

        :param query_db: orm 对象
        :return: 资产单位列表信息对象
        """
        property_unit_list_result = await PropertyUnitDao.get_all_property_unit_list(query_db)

        return CamelCaseUtil.transform_result(property_unit_list_result)

    @classmethod
    async def check_property_unit_title_unique_services(
            cls, query_db: AsyncSession, page_object: PropertyUnitModel
    ) -> bool:
        """
        校验资产单位名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 资产单位对象
        :return: 校验结果
        """
        property_unit_id = -1 if page_object.id is None else page_object.id
        property_unit = await PropertyUnitDao.get_property_unit_detail_by_info(query_db, page_object)
        if property_unit and property_unit.id != property_unit_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_property_unit_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddPropertyUnitModel
    ) -> CrudResponseModel:
        """
        新增资产单位信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增资产单位对象
        :return: 新增资产单位校验结果
        """
        if not await cls.check_property_unit_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增单位{page_object.title}失败，单位名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_property_unit = PropertyUnitModel(
                title=page_object.title,
                sort=page_object.sort if page_object.sort is not None else 0,
                desc=page_object.desc,
                status=page_object.status if page_object.status is not None else 1,
                create_time=current_time,
                update_time=current_time
            )
            await PropertyUnitDao.add_property_unit_dao(query_db, add_property_unit)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_property_unit_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPropertyUnitModel
    ) -> CrudResponseModel:
        """
        编辑资产单位信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑资产单位对象
        :return: 编辑资产单位校验结果
        """
        edit_property_unit = page_object.model_dump(exclude_unset=True)
        property_unit_info = await cls.property_unit_detail_services(query_db, page_object.id)

        if property_unit_info.id:
            if not await cls.check_property_unit_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改单位{page_object.title}失败，单位名称已存在')

            try:
                edit_property_unit['update_time'] = int(datetime.now().timestamp())
                await PropertyUnitDao.edit_property_unit_dao(query_db, edit_property_unit)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='单位不存在')

    @classmethod
    async def delete_property_unit_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeletePropertyUnitModel
    ) -> CrudResponseModel:
        """
        删除资产单位信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除资产单位对象
        :return: 删除资产单位校验结果
        """
        if page_object.id:
            try:
                property_unit = await cls.property_unit_detail_services(query_db, page_object.id)
                if not property_unit.id:
                    raise ServiceException(message='单位不存在')

                update_time = int(datetime.now().timestamp())
                await PropertyUnitDao.delete_property_unit_dao(
                    query_db,
                    PropertyUnitModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入单位 id 为空')

    @classmethod
    async def set_property_unit_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPropertyUnitModel
    ) -> CrudResponseModel:
        """
        设置资产单位状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置资产单位状态对象
        :return: 设置资产单位状态校验结果
        """
        property_unit_info = await cls.property_unit_detail_services(query_db, page_object.id)

        if property_unit_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await PropertyUnitDao.disable_property_unit_dao(
                        query_db,
                        PropertyUnitModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await PropertyUnitDao.enable_property_unit_dao(
                        query_db,
                        PropertyUnitModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='单位不存在')

    @classmethod
    async def property_unit_detail_services(cls, query_db: AsyncSession, property_unit_id: int) -> PropertyUnitModel:
        """
        获取资产单位详细信息 service

        :param query_db: orm 对象
        :param property_unit_id: 单位 ID
        :return: 单位 ID 对应的信息
        """
        property_unit = await PropertyUnitDao.get_property_unit_detail_by_id(query_db, property_unit_id)
        result = PropertyUnitModel(**CamelCaseUtil.transform_result(property_unit)) if property_unit else PropertyUnitModel()

        return result
