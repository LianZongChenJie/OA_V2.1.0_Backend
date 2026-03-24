from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.note_cate_dao import NoteCateDao
from module_admin.entity.vo.note_cate_vo import (
    AddNoteCateModel,
    DeleteNoteCateModel,
    EditNoteCateModel,
    NoteCateModel,
    NoteCatePageQueryModel,
    SetNoteCateModel,
)
from utils.common_util import CamelCaseUtil


class NoteCateService:
    """
    公告分类管理模块服务层
    """

    @classmethod
    async def get_note_cate_list_services(
            cls, query_db: AsyncSession, query_object: NoteCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取公告分类列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 公告分类列表信息对象
        """
        note_cate_list_result = await NoteCateDao.get_note_cate_list(query_db, query_object, is_page)

        return note_cate_list_result

    @classmethod
    async def check_note_cate_title_unique_services(
            cls, query_db: AsyncSession, page_object: NoteCateModel
    ) -> bool:
        """
        校验公告分类名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 公告分类对象
        :return: 校验结果
        """
        note_cate_id = -1 if page_object.id is None else page_object.id
        note_cate = await NoteCateDao.get_note_cate_detail_by_info(query_db, page_object)
        if note_cate and note_cate.id != note_cate_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_note_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddNoteCateModel
    ) -> CrudResponseModel:
        """
        新增公告分类信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增公告分类对象
        :return: 新增公告分类校验结果
        """
        if not await cls.check_note_cate_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增公告分类{page_object.title}失败，公告分类名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_note_cate = NoteCateModel(
                pid=page_object.pid if page_object.pid is not None else 0,
                sort=page_object.sort if page_object.sort is not None else 0,
                title=page_object.title,
                status=page_object.status if page_object.status is not None else 1,
                create_time=current_time,
                update_time=current_time
            )
            await NoteCateDao.add_note_cate_dao(query_db, add_note_cate)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_note_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditNoteCateModel
    ) -> CrudResponseModel:
        """
        编辑公告分类信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑公告分类对象
        :return: 编辑公告分类校验结果
        """
        edit_note_cate = page_object.model_dump(exclude_unset=True)
        note_cate_info = await cls.note_cate_detail_services(query_db, page_object.id)

        if note_cate_info.id:
            if not await cls.check_note_cate_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改公告分类{page_object.title}失败，公告分类名称已存在')

            try:
                edit_note_cate['update_time'] = int(datetime.now().timestamp())
                await NoteCateDao.edit_note_cate_dao(query_db, edit_note_cate)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='公告分类不存在')

    @classmethod
    async def delete_note_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteNoteCateModel
    ) -> CrudResponseModel:
        """
        删除公告分类信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除公告分类对象
        :return: 删除公告分类校验结果
        """
        note_cate_info = await cls.note_cate_detail_services(query_db, page_object.id)

        if not note_cate_info.id:
            raise ServiceException(message='公告分类不存在')

        try:
            update_time = int(datetime.now().timestamp())
            await NoteCateDao.delete_note_cate_dao(
                query_db,
                NoteCateModel(id=page_object.id, status=-1, update_time=update_time)
            )
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def set_note_cate_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: SetNoteCateModel
    ) -> CrudResponseModel:
        """
        设置公告分类状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置公告分类状态对象
        :return: 设置公告分类状态校验结果
        """
        note_cate_info = await cls.note_cate_detail_services(query_db, page_object.id)

        if not note_cate_info.id:
            raise ServiceException(message='公告分类不存在')

        try:
            update_time = int(datetime.now().timestamp())

            if page_object.status == 0:
                await NoteCateDao.disable_note_cate_dao(
                    query_db,
                    NoteCateModel(id=page_object.id, update_time=update_time)
                )
            elif page_object.status == 1:
                await NoteCateDao.enable_note_cate_dao(
                    query_db,
                    NoteCateModel(id=page_object.id, update_time=update_time)
                )

            await query_db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def note_cate_detail_services(cls, query_db: AsyncSession, note_cate_id: int) -> NoteCateModel:
        """
        获取公告分类详细信息 service

        :param query_db: orm 对象
        :param note_cate_id: 公告分类 id
        :return: 公告分类 id 对应的信息
        """
        note_cate = await NoteCateDao.get_note_cate_detail_by_id(query_db, note_cate_id)
        result = NoteCateModel(**CamelCaseUtil.transform_result(note_cate)) if note_cate else NoteCateModel()

        return result

