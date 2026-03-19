from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.seal_cate_dao import SealCateDao
from module_admin.entity.vo.seal_cate_vo import (
    AddSealCateModel,
    DeleteSealCateModel,
    EditSealCateModel,
    SealCateModel,
    SealCatePageQueryModel,
)
from utils.common_util import CamelCaseUtil


class SealCateService:
    """
    印章类别管理模块服务层
    """

    @classmethod
    async def get_seal_cate_list_services(
            cls, query_db: AsyncSession, query_object: SealCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取印章类别列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 印章类别列表信息对象
        """
        seal_cate_list_result = await SealCateDao.get_seal_cate_list(query_db, query_object, is_page)

        return seal_cate_list_result

    @classmethod
    async def check_seal_cate_title_unique_services(
            cls, query_db: AsyncSession, page_object: SealCateModel
    ) -> bool:
        """
        校验印章类别名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 印章类别对象
        :return: 校验结果
        """
        seal_cate_id = -1 if page_object.id is None else page_object.id
        seal_cate = await SealCateDao.get_seal_cate_detail_by_info(query_db, page_object)
        if seal_cate and seal_cate.id != seal_cate_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_seal_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddSealCateModel
    ) -> CrudResponseModel:
        """
        新增印章类别信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增印章类别对象
        :return: 新增印章类别校验结果
        """
        if not await cls.check_seal_cate_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增印章类别{page_object.title}失败，印章名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_seal_cate = SealCateModel(
                title=page_object.title,
                dids=page_object.dids if page_object.dids is not None else '',
                keep_uid=page_object.keep_uid if page_object.keep_uid is not None else 0,
                status=page_object.status if page_object.status is not None else 1,
                remark=page_object.remark if page_object.remark is not None else '',
                create_time=current_time,
                update_time=current_time
            )
            await SealCateDao.add_seal_cate_dao(query_db, add_seal_cate)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_seal_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditSealCateModel
    ) -> CrudResponseModel:
        """
        编辑印章类别信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑印章类别对象
        :return: 编辑印章类别校验结果
        """
        edit_seal_cate = page_object.model_dump(exclude_unset=True)
        seal_cate_info = await cls.seal_cate_detail_services(query_db, page_object.id)

        if seal_cate_info.id:
            if not await cls.check_seal_cate_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改印章类别{page_object.title}失败，印章名称已存在')

            try:
                edit_seal_cate['update_time'] = int(datetime.now().timestamp())
                await SealCateDao.edit_seal_cate_dao(query_db, edit_seal_cate)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='印章类别不存在')

    @classmethod
    async def delete_seal_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteSealCateModel
    ) -> CrudResponseModel:
        """
        删除印章类别信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除印章类别对象
        :return: 删除印章类别校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for seal_cate_id in id_list:
                    seal_cate = await cls.seal_cate_detail_services(query_db, int(seal_cate_id))
                    if not seal_cate.id:
                        raise ServiceException(message='印章类别不存在')

                    update_time = int(datetime.now().timestamp())
                    await SealCateDao.delete_seal_cate_dao(
                        query_db,
                        SealCateModel(id=int(seal_cate_id), update_time=update_time)
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入印章类别 id 为空')

    @classmethod
    async def set_seal_cate_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditSealCateModel
    ) -> CrudResponseModel:
        """
        设置印章类别状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置印章类别状态对象
        :return: 设置印章类别状态校验结果
        """
        seal_cate_info = await cls.seal_cate_detail_services(query_db, page_object.id)

        if seal_cate_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await SealCateDao.disable_seal_cate_dao(
                        query_db,
                        SealCateModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await SealCateDao.enable_seal_cate_dao(
                        query_db,
                        SealCateModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='印章类别不存在')

    @classmethod
    async def seal_cate_detail_services(cls, query_db: AsyncSession, seal_cate_id: int) -> SealCateModel:
        """
        获取印章类别详细信息 service

        :param query_db: orm 对象
        :param seal_cate_id: 印章类别 id
        :return: 印章类别 id 对应的信息
        """
        seal_cate = await SealCateDao.get_seal_cate_detail_by_id(query_db, seal_cate_id)
        result = SealCateModel(**CamelCaseUtil.transform_result(seal_cate)) if seal_cate else SealCateModel()

        return result

