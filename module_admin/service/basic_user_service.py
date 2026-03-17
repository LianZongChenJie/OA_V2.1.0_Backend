from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.basic_user_dao import BasicUserDao
from module_admin.entity.vo.basic_user_vo import (
    AddBasicUserModel,
    DeleteBasicUserModel,
    EditBasicUserModel,
    BasicUserModel,
    BasicUserPageQueryModel,
)
from utils.common_util import CamelCaseUtil


class BasicUserService:
    """
    人事模块常规数据管理服务层
    """

    @classmethod
    async def get_basic_user_list_services(
            cls, query_db: AsyncSession, query_object: BasicUserPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取人事模块常规数据列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 人事模块常规数据列表信息对象
        """
        basic_user_list_result = await BasicUserDao.get_basic_user_list(query_db, query_object, is_page)

        return basic_user_list_result

    @classmethod
    async def check_basic_user_title_unique_services(
            cls, query_db: AsyncSession, page_object: BasicUserModel
    ) -> bool:
        """
        校验人事模块常规数据名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 人事模块常规数据对象
        :return: 校验结果
        """
        basic_user_id = -1 if page_object.id is None else page_object.id
        basic_user = await BasicUserDao.get_basic_user_detail_by_info(query_db, page_object)
        if basic_user and basic_user.id != basic_user_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_basic_user_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddBasicUserModel
    ) -> CrudResponseModel:
        """
        新增人事模块常规数据信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增人事模块常规数据对象
        :return: 新增人事模块常规数据校验结果
        """
        if not await cls.check_basic_user_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增{page_object.title}失败，名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_basic_user = BasicUserModel(
                types=page_object.types,
                title=page_object.title,
                status=page_object.status if page_object.status is not None else 1,
                create_time=current_time,
                update_time=current_time
            )
            await BasicUserDao.add_basic_user_dao(query_db, add_basic_user)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_basic_user_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditBasicUserModel
    ) -> CrudResponseModel:
        """
        编辑人事模块常规数据信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑人事模块常规数据对象
        :return: 编辑人事模块常规数据校验结果
        """
        edit_basic_user = page_object.model_dump(exclude_unset=True)
        basic_user_info = await cls.basic_user_detail_services(query_db, page_object.id)

        if basic_user_info.id:
            if not await cls.check_basic_user_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改{page_object.title}失败，名称已存在')

            try:
                edit_basic_user['update_time'] = int(datetime.now().timestamp())
                await BasicUserDao.edit_basic_user_dao(query_db, edit_basic_user)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='数据不存在')

    @classmethod
    async def delete_basic_user_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteBasicUserModel
    ) -> CrudResponseModel:
        """
        删除人事模块常规数据信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除人事模块常规数据对象
        :return: 删除人事模块常规数据校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for basic_user_id in id_list:
                    basic_user = await cls.basic_user_detail_services(query_db, int(basic_user_id))
                    if not basic_user.id:
                        raise ServiceException(message='数据不存在')

                    update_time = int(datetime.now().timestamp())
                    await BasicUserDao.delete_basic_user_dao(
                        query_db,
                        BasicUserModel(id=int(basic_user_id), update_time=update_time)
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入数据 id 为空')

    @classmethod
    async def set_basic_user_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditBasicUserModel
    ) -> CrudResponseModel:
        """
        设置人事模块常规数据状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置人事模块常规数据状态对象
        :return: 设置人事模块常规数据状态校验结果
        """
        basic_user_info = await cls.basic_user_detail_services(query_db, page_object.id)

        if basic_user_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await BasicUserDao.disable_basic_user_dao(
                        query_db,
                        BasicUserModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await BasicUserDao.enable_basic_user_dao(
                        query_db,
                        BasicUserModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='数据不存在')

    @classmethod
    async def basic_user_detail_services(cls, query_db: AsyncSession, basic_user_id: int) -> BasicUserModel:
        """
        获取人事模块常规数据详细信息 service

        :param query_db: orm 对象
        :param basic_user_id: 数据 ID
        :return: 数据 ID 对应的信息
        """
        basic_user = await BasicUserDao.get_basic_user_detail_by_id(query_db, basic_user_id)
        result = BasicUserModel(**CamelCaseUtil.transform_result(basic_user)) if basic_user else BasicUserModel()

        return result

