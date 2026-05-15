from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from common.constant import CommonConstant
from exceptions.exception import ServiceException
from module_personnel.dao.flow_record_dao import FlowRecordDao
from module_personnel.dao.talent_dao import TalentDao
from sqlalchemy.sql import ColumnElement
from module_personnel.entity.vo.talent_vo import OaTalentBaseModel, \
    OaTalentPageQueryModel, OaTalentDetailModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime
from utils.camel_converter import ModelConverter
from utils.timeformat import int_time


class TalentService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaTalentPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaTalentBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await TalentDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaTalentBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaTalentBaseModel) -> CrudResponseModel:
        if model.id:
            return await cls.update_service(query_db, model)
        try:
            model.create_time = int(datetime.now().timestamp())
            model.status = 1
            model.entry_time = int_time(model.entry_time)
            change = await TalentDao.add(query_db, model)
            model.remark = '提交了离职申请'
            await cls.add_record(query_db, change, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"新增失败")

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaTalentBaseModel) -> CrudResponseModel:
        try:
            model.update_time = int(datetime.now().timestamp())
            change = await TalentDao.update(query_db, model)
            await cls.add_record(query_db, change, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='编辑成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"编辑失败")


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaTalentDetailModel:
        try:
            detail = OaTalentDetailModel()
            info = await TalentDao.get_info_by_id(query_db, id)
            records = await FlowRecordDao.get_records_dict(query_db, info.id, info.check_flow_id)
            detail = {}
            detail.update(info)
            detail['records'] = records
            if not detail:
                raise ServiceException(message="未找到该数据")
            return ModelConverter.convert_to_camel_case(detail)
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f"查询失败")

    @classmethod
    async def check_unique_services(cls, query_db: AsyncSession, page_object: OaTalentBaseModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        title = -1 if page_object.uid is None else page_object.uid
        model = await TalentDao.get_info_by_uid(query_db, page_object)
        if model and model.id == page_object.id:
            return CommonConstant.UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            talent = await TalentDao.get_info_by_id(db, id)
            if talent.check_status != 0 or talent.check_status != 4:
                raise CrudResponseModel(is_success=False, message='请先撤销申请再删除')
            await TalentDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise ServiceException(message=f"删除失败")
