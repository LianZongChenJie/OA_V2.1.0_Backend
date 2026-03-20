from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.services_dao import ServicesDao
from module_admin.entity.vo.services_vo import (
    AddServicesModel,
    DeleteServicesModel,
    EditServicesModel,
    ServicesModel,
    ServicesPageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class ServicesService:
    """
    服务管理模块服务层
    """

    @classmethod
    async def get_services_list_services(
            cls, query_db: AsyncSession, query_object: ServicesPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取服务列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 服务列表信息对象
        """
        services_list_result = await ServicesDao.get_services_list(query_db, query_object, is_page)

        return services_list_result

    @classmethod
    async def check_services_title_unique_services(
            cls, query_db: AsyncSession, page_object: ServicesModel
    ) -> bool:
        """
        校验服务名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 服务对象
        :return: 校验结果
        """
        services_id = -1 if page_object.id is None else page_object.id
        services = await ServicesDao.get_services_detail_by_info(query_db, page_object)
        if services and services.id != services_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_services_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddServicesModel
    ) -> CrudResponseModel:
        """
        新增服务信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增服务对象
        :return: 新增服务校验结果
        """
        if not await cls.check_services_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增服务{page_object.title}失败，服务名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_services = ServicesModel(
                title=page_object.title,
                cate_id=page_object.cate_id if page_object.cate_id is not None else 0,
                price=page_object.price if page_object.price is not None else 0.00,
                content=page_object.content,
                sort=page_object.sort if page_object.sort is not None else 0,
                status=page_object.status if page_object.status is not None else 1,
                create_time=current_time,
                update_time=current_time,
                delete_time=0
            )
            logger.info(f'Service 层准备插入的数据：title={add_services.title}, create_time={add_services.create_time}, update_time={add_services.update_time}, delete_time={add_services.delete_time}')
            await ServicesDao.add_services_dao(query_db, add_services)
            await query_db.commit()
            logger.info(f'新增成功，生成的 ID: {add_services.id}')
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_services_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditServicesModel
    ) -> CrudResponseModel:
        """
        编辑服务信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑服务对象
        :return: 编辑服务校验结果
        """
        edit_services = page_object.model_dump(exclude_unset=True)
        services_info = await cls.services_detail_services(query_db, page_object.id)

        if services_info.id:
            if not await cls.check_services_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改服务{page_object.title}失败，服务名称已存在')

            try:
                edit_services['update_time'] = int(datetime.now().timestamp())
                await ServicesDao.edit_services_dao(query_db, edit_services)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='服务不存在')

    @classmethod
    async def delete_services_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteServicesModel
    ) -> CrudResponseModel:
        """
        删除服务信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除服务对象
        :return: 删除服务校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for services_id in id_list:
                    services = await cls.services_detail_services(query_db, int(services_id))
                    if not services.id:
                        raise ServiceException(message='服务不存在')

                    update_time = int(datetime.now().timestamp())
                    await ServicesDao.delete_services_dao(
                        query_db,
                        ServicesModel(id=int(services_id), update_time=update_time),
                        page_object.type
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入服务 id 为空')

    @classmethod
    async def set_services_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditServicesModel
    ) -> CrudResponseModel:
        """
        设置服务状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置服务对象
        :return: 设置服务状态校验结果
        """
        services_info = await cls.services_detail_services(query_db, page_object.id)

        if services_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await ServicesDao.disable_services_dao(
                        query_db,
                        ServicesModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await ServicesDao.enable_services_dao(
                        query_db,
                        ServicesModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='服务不存在')

    @classmethod
    async def services_detail_services(cls, query_db: AsyncSession, services_id: int) -> ServicesModel:
        """
        获取服务详细信息 service

        :param query_db: orm 对象
        :param services_id: 服务 id
        :return: 服务 id 对应的信息
        """
        services = await ServicesDao.get_services_detail_by_id(query_db, services_id)
        result = ServicesModel(**CamelCaseUtil.transform_result(services)) if services else ServicesModel()

        return result
