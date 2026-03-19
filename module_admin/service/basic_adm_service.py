from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from typing import Any
from datetime import datetime
from fastapi import Request
from common.vo import PageModel, CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.dao.basic_adm_dao import BasicAdmDao
from module_admin.entity.vo.basic_adm_vo import BasicAdmPageQueryModel, OaBasicAdmModel, EditBasicAdmModel, DeleteBasicAdmModel
from utils.common_util import CamelCaseUtil


class BasicAdmService:
    @classmethod
    async def get_basic_adm_list_services(cls, query_db: AsyncSession, query_object: BasicAdmPageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[OaBasicAdmModel] | list[dict[str, Any]]:
        query_list = await BasicAdmDao.get_basic_adm_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            basic_adm_list_result = PageModel[OaBasicAdmModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            basic_adm_list_result = []
            if query_list:
                basic_adm_list_result = [{**row} for row in query_list]
        return basic_adm_list_result

    @classmethod
    async def check_basic_adm_title_unique_services(cls, query_db: AsyncSession, page_object: OaBasicAdmModel) -> bool:
        basic_adm_id = -1 if page_object.id is None else page_object.id
        basic_adm = await BasicAdmDao.get_basic_adm_info(query_db, page_object.id) if page_object.id else None
        if basic_adm and basic_adm.id != basic_adm_id:
            return False
        return True

    @classmethod
    async def add_basic_adm_service(cls, request: Request, query_db: AsyncSession, basic_adm_model: OaBasicAdmModel) -> CrudResponseModel:
        try:
            if not await cls.check_basic_adm_title_unique_services(query_db, basic_adm_model):
                raise ServiceException(message=f'新增行政模块常规数据{basic_adm_model.title}失败，名称已存在')

            current_time = int(datetime.now().timestamp())
            basic_adm_model.create_time = current_time
            basic_adm_model.update_time = current_time
            await BasicAdmDao.add_basic_adm(query_db, basic_adm_model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def update_basic_adm_service(cls, request: Request, query_db: AsyncSession, basic_adm_model: OaBasicAdmModel) -> CrudResponseModel:
        try:
            if not await cls.check_basic_adm_title_unique_services(query_db, basic_adm_model):
                raise ServiceException(message=f'修改行政模块常规数据{basic_adm_model.title}失败，名称已存在')

            basic_adm_model.update_time = int(datetime.now().timestamp())
            await BasicAdmDao.update_basic_adm(query_db, basic_adm_model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_basic_adm_service(cls, request: Request, query_db: AsyncSession, page_object: DeleteBasicAdmModel) -> CrudResponseModel:
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for basic_adm_id in id_list:
                    basic_adm = await cls.basic_adm_detail_services(query_db, int(basic_adm_id))
                    if not basic_adm.id:
                        raise ServiceException(message='行政模块常规数据不存在')

                    await BasicAdmDao.delete_basic_adm(query_db, int(basic_adm_id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入行政模块常规数据 id 为空')

    @classmethod
    async def set_basic_adm_status_services(cls, request: Request, query_db: AsyncSession, page_object: EditBasicAdmModel) -> CrudResponseModel:
        basic_adm_info = await cls.basic_adm_detail_services(query_db, page_object.id)

        if basic_adm_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await BasicAdmDao.change_status_basic_adm(query_db, page_object)
                elif page_object.status == 1:
                    await BasicAdmDao.change_status_basic_adm(query_db, page_object)

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='行政模块常规数据不存在')

    @classmethod
    async def basic_adm_detail_services(cls, query_db: AsyncSession, basic_adm_id: int) -> OaBasicAdmModel:
        basic_adm = await BasicAdmDao.get_basic_adm_info(query_db, basic_adm_id)
        result = OaBasicAdmModel(**CamelCaseUtil.transform_result(basic_adm)) if basic_adm else OaBasicAdmModel()
        return result

