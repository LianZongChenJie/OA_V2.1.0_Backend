from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.care_cate_dao import CareCateDao
from module_admin.entity.vo.care_cate_vo import (
    AddCareCateModel,
    DeleteCareCateModel,
    EditCareCateModel,
    CareCateModel,
    CareCatePageQueryModel,
)
from utils.common_util import CamelCaseUtil


class CareCateService:
    """
    关怀项目管理模块服务层
    """

    @classmethod
    async def get_care_cate_list_services(
            cls, query_db: AsyncSession, query_object: CareCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取关怀项目列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 关怀项目列表信息对象
        """
        care_cate_list_result = await CareCateDao.get_care_cate_list(query_db, query_object, is_page)

        return care_cate_list_result

    @classmethod
    async def check_care_cate_title_unique_services(
            cls, query_db: AsyncSession, page_object: CareCateModel
    ) -> bool:
        """
        校验关怀项目名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 关怀项目对象
        :return: 校验结果
        """
        care_cate_id = -1 if page_object.id is None else page_object.id
        care_cate = await CareCateDao.get_care_cate_detail_by_info(query_db, page_object)
        if care_cate and care_cate.id != care_cate_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_care_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddCareCateModel
    ) -> CrudResponseModel:
        """
        新增关怀项目信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增关怀项目对象
        :return: 新增关怀项目校验结果
        """
        if not await cls.check_care_cate_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增关怀项目{page_object.title}失败，关怀项目名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_care_cate = CareCateModel(
                title=page_object.title,
                status=page_object.status if page_object.status is not None else 1,
                create_time=current_time,
                update_time=current_time
            )
            await CareCateDao.add_care_cate_dao(query_db, add_care_cate)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_care_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCareCateModel
    ) -> CrudResponseModel:
        """
        编辑关怀项目信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑关怀项目对象
        :return: 编辑关怀项目校验结果
        """
        edit_care_cate = page_object.model_dump(exclude_unset=True)
        care_cate_info = await cls.care_cate_detail_services(query_db, page_object.id)

        if care_cate_info.id:
            if not await cls.check_care_cate_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改关怀项目{page_object.title}失败，关怀项目名称已存在')

            try:
                edit_care_cate['update_time'] = int(datetime.now().timestamp())
                await CareCateDao.edit_care_cate_dao(query_db, edit_care_cate)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='关怀项目不存在')

    @classmethod
    async def delete_care_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteCareCateModel
    ) -> CrudResponseModel:
        """
        删除关怀项目信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除关怀项目对象
        :return: 删除关怀项目校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for care_cate_id in id_list:
                    care_cate = await cls.care_cate_detail_services(query_db, int(care_cate_id))
                    if not care_cate.id:
                        raise ServiceException(message='关怀项目不存在')

                    update_time = int(datetime.now().timestamp())
                    await CareCateDao.delete_care_cate_dao(
                        query_db,
                        CareCateModel(id=int(care_cate_id), update_time=update_time)
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入关怀项目 id 为空')

    @classmethod
    async def set_care_cate_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCareCateModel
    ) -> CrudResponseModel:
        """
        设置关怀项目状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置关怀项目状态对象
        :return: 设置关怀项目状态校验结果
        """
        care_cate_info = await cls.care_cate_detail_services(query_db, page_object.id)

        if care_cate_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await CareCateDao.disable_care_cate_dao(
                        query_db,
                        CareCateModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await CareCateDao.enable_care_cate_dao(
                        query_db,
                        CareCateModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='关怀项目不存在')

    @classmethod
    async def care_cate_detail_services(cls, query_db: AsyncSession, care_cate_id: int) -> CareCateModel:
        """
        获取关怀项目详细信息 service

        :param query_db: orm 对象
        :param care_cate_id: 关怀项目 id
        :return: 关怀项目 id 对应的信息
        """
        care_cate = await CareCateDao.get_care_cate_detail_by_id(query_db, care_cate_id)
        result = CareCateModel(**CamelCaseUtil.transform_result(care_cate)) if care_cate else CareCateModel()

        return result

