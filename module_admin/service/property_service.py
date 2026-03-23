from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.property_dao import PropertyDao
from module_admin.entity.vo.property_vo import (
    AddPropertyModel,
    DeletePropertyModel,
    EditPropertyModel,
    PropertyModel,
    PropertyPageQueryModel,
)
from utils.common_util import CamelCaseUtil

class PropertyService:
    """
    资产管理服务层
    """

    @classmethod
    async def get_property_list_services(
            cls, query_db: AsyncSession, query_object: PropertyPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取资产列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 资产列表信息对象
        """
        property_list_result = await PropertyDao.get_property_list(query_db, query_object, is_page)

        return property_list_result

    @classmethod
    async def get_all_property_list_services(cls, query_db: AsyncSession) -> list[dict[str, Any]]:
        """
        获取所有资产列表信息 service

        :param query_db: orm 对象
        :return: 资产列表信息对象
        """
        property_list_result = await PropertyDao.get_all_property_list(query_db)

        return CamelCaseUtil.transform_result(property_list_result)

    @classmethod
    async def check_property_title_unique_services(
            cls, query_db: AsyncSession, page_object: PropertyModel
    ) -> bool:
        """
        校验资产名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 资产对象
        :return: 校验结果
        """
        property_id = -1 if page_object.id is None else page_object.id
        property = await PropertyDao.get_property_detail_by_info(query_db, page_object)
        if property and property.id != property_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_property_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddPropertyModel
    ) -> CrudResponseModel:
        """
        新增资产信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增资产对象
        :return: 新增资产校验结果
        """
        if not await cls.check_property_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增资产{page_object.title}失败，资产名称已存在')

        try:
            current_time = int(datetime.now().timestamp() * 1000)
            add_property = PropertyModel(
                title=page_object.title,
                code=page_object.code,
                thumb=page_object.thumb,
                cate_id=page_object.cate_id,
                brand_id=page_object.brand_id,
                unit_id=page_object.unit_id,
                quality_time=page_object.quality_time,
                buy_time=page_object.buy_time,
                price=page_object.price,
                rate=page_object.rate,
                model_=page_object.model_,
                address=page_object.address,
                user_dids=page_object.user_dids,
                user_ids=page_object.user_ids,
                content=page_object.content,
                file_ids=page_object.file_ids,
                source=page_object.source if page_object.source is not None else 1,
                purchase_id=page_object.purchase_id,
                status=page_object.status if page_object.status is not None else 1,
                admin_id=page_object.admin_id if page_object.admin_id is not None else 0,
                create_time=current_time,
                update_time=current_time
            )
            await PropertyDao.add_property_dao(query_db, add_property)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_property_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPropertyModel
    ) -> CrudResponseModel:
        """
        编辑资产信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑资产对象
        :return: 编辑资产校验结果
        """
        edit_property = page_object.model_dump(exclude_unset=True)
        property_info = await cls.property_detail_services(query_db, page_object.id)

        if property_info.id:
            if not await cls.check_property_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改资产{page_object.title}失败，资产名称已存在')

            try:
                edit_property['update_time'] = int(datetime.now().timestamp())
                await PropertyDao.edit_property_dao(query_db, edit_property)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='资产不存在')

    @classmethod
    async def delete_property_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeletePropertyModel
    ) -> CrudResponseModel:
        """
        删除资产信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除资产对象
        :return: 删除资产校验结果
        """
        if page_object.id:
            try:
                property = await cls.property_detail_services(query_db, page_object.id)
                if not property.id:
                    raise ServiceException(message='资产不存在')

                update_time = int(datetime.now().timestamp())
                await PropertyDao.delete_property_dao(
                    query_db,
                    PropertyModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入资产 id 为空')

    @classmethod
    async def set_property_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPropertyModel
    ) -> CrudResponseModel:
        """
        设置资产状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置资产状态对象
        :return: 设置资产状态校验结果
        """
        property_info = await cls.property_detail_services(query_db, page_object.id)

        if property_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await PropertyDao.disable_property_dao(
                        query_db,
                        PropertyModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await PropertyDao.enable_property_dao(
                        query_db,
                        PropertyModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='资产不存在')

    @classmethod
    async def property_detail_services(cls, query_db: AsyncSession, property_id: int) -> PropertyModel:
        """
        获取资产详细信息 service

        :param query_db: orm 对象
        :param property_id: 资产 ID
        :return: 资产 ID 对应的信息
        """
        property = await PropertyDao.get_property_detail_by_id(query_db, property_id)
        result = PropertyModel(**CamelCaseUtil.transform_result(property)) if property else PropertyModel()

        return result