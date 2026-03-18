from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.property_brand_dao import PropertyBrandDao
from module_admin.entity.vo.property_brand_vo import (
    AddPropertyBrandModel,
    DeletePropertyBrandModel,
    EditPropertyBrandModel,
    PropertyBrandModel,
    PropertyBrandPageQueryModel,
)
from utils.common_util import CamelCaseUtil


class PropertyBrandService:
    """
    资产品牌管理服务层
    """

    @classmethod
    async def get_property_brand_list_services(
            cls, query_db: AsyncSession, query_object: PropertyBrandPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取资产品牌列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 资产品牌列表信息对象
        """
        property_brand_list_result = await PropertyBrandDao.get_property_brand_list(query_db, query_object, is_page)

        return property_brand_list_result

    @classmethod
    async def get_all_property_brand_list_services(cls, query_db: AsyncSession) -> list[dict[str, Any]]:
        """
        获取所有资产品牌列表信息 service

        :param query_db: orm 对象
        :return: 资产品牌列表信息对象
        """
        property_brand_list_result = await PropertyBrandDao.get_all_property_brand_list(query_db)

        return CamelCaseUtil.transform_result(property_brand_list_result)

    @classmethod
    async def check_property_brand_title_unique_services(
            cls, query_db: AsyncSession, page_object: PropertyBrandModel
    ) -> bool:
        """
        校验资产品牌名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 资产品牌对象
        :return: 校验结果
        """
        property_brand_id = -1 if page_object.id is None else page_object.id
        property_brand = await PropertyBrandDao.get_property_brand_detail_by_info(query_db, page_object)
        if property_brand and property_brand.id != property_brand_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_property_brand_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddPropertyBrandModel
    ) -> CrudResponseModel:
        """
        新增资产品牌信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增资产品牌对象
        :return: 新增资产品牌校验结果
        """
        if not await cls.check_property_brand_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增品牌{page_object.title}失败，品牌名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_property_brand = PropertyBrandModel(
                title=page_object.title,
                sort=page_object.sort if page_object.sort is not None else 0,
                desc=page_object.desc,
                status=page_object.status if page_object.status is not None else 1,
                create_time=current_time,
                update_time=current_time
            )
            await PropertyBrandDao.add_property_brand_dao(query_db, add_property_brand)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_property_brand_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPropertyBrandModel
    ) -> CrudResponseModel:
        """
        编辑资产品牌信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑资产品牌对象
        :return: 编辑资产品牌校验结果
        """
        edit_property_brand = page_object.model_dump(exclude_unset=True)
        property_brand_info = await cls.property_brand_detail_services(query_db, page_object.id)

        if property_brand_info.id:
            if not await cls.check_property_brand_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改品牌{page_object.title}失败，品牌名称已存在')

            try:
                edit_property_brand['update_time'] = int(datetime.now().timestamp())
                await PropertyBrandDao.edit_property_brand_dao(query_db, edit_property_brand)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='品牌不存在')

    @classmethod
    async def delete_property_brand_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeletePropertyBrandModel
    ) -> CrudResponseModel:
        """
        删除资产品牌信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除资产品牌对象
        :return: 删除资产品牌校验结果
        """
        if page_object.id:
            try:
                property_brand = await cls.property_brand_detail_services(query_db, page_object.id)
                if not property_brand.id:
                    raise ServiceException(message='品牌不存在')

                update_time = int(datetime.now().timestamp())
                await PropertyBrandDao.delete_property_brand_dao(
                    query_db,
                    PropertyBrandModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入品牌 id 为空')

    @classmethod
    async def set_property_brand_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPropertyBrandModel
    ) -> CrudResponseModel:
        """
        设置资产品牌状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置资产品牌状态对象
        :return: 设置资产品牌状态校验结果
        """
        property_brand_info = await cls.property_brand_detail_services(query_db, page_object.id)

        if property_brand_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await PropertyBrandDao.disable_property_brand_dao(
                        query_db,
                        PropertyBrandModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await PropertyBrandDao.enable_property_brand_dao(
                        query_db,
                        PropertyBrandModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='品牌不存在')

    @classmethod
    async def property_brand_detail_services(cls, query_db: AsyncSession, property_brand_id: int) -> PropertyBrandModel:
        """
        获取资产品牌详细信息 service

        :param query_db: orm 对象
        :param property_brand_id: 品牌 ID
        :return: 品牌 ID 对应的信息
        """
        property_brand = await PropertyBrandDao.get_property_brand_detail_by_id(query_db, property_brand_id)
        result = PropertyBrandModel(**CamelCaseUtil.transform_result(property_brand)) if property_brand else PropertyBrandModel()

        return result
