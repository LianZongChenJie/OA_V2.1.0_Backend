from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from common.constant import CommonConstant
from exceptions.exception import ServiceException
from module_personnel.dao.rewards_dao import RewardsDao
from module_personnel.entity.do.rewards_do import OaRewards
from sqlalchemy.sql import ColumnElement
from module_personnel.entity.vo.rewards_vo import OaRewardsBaseModel, OaRewardsPageQueryModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime


class RewardsService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaRewardsPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaRewardsBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await RewardsDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaRewardsBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaRewardsBaseModel) -> CrudResponseModel:
        try:
            model.create_time = int(datetime.now().timestamp())
            model.status = 1
            rewards = await RewardsDao.add(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaRewardsBaseModel) -> CrudResponseModel:
        try:
            model.update_time = int(datetime.now().timestamp())
            change = await RewardsDao.update(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaRewardsBaseModel:
        try:
            info = await RewardsDao.get_info_by_id(query_db, id)
            if not info:
                raise ServiceException(message="未找到该数据")
            return info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def check_unique_services(cls, query_db: AsyncSession, page_object: OaRewardsBaseModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        title = -1 if page_object.uid is None else page_object.uid
        model = await RewardsDao.get_info_by_uid(query_db, page_object)
        if model and model.id == page_object.id:
            return CommonConstant.UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            await RewardsDao.del_by_id(db, id)
        except Exception as e:
            await db.rollback()
            raise e