from unittest.mock import seal

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from common.constant import CommonConstant
from exceptions.exception import ServiceException
from module_basicdata.dao.public.flow_step_dao import OaFlowStepDao
from module_administrative.dao.seal_dao import SealDao
from module_personnel.dao.flow_record_dao import FlowRecordDao
from module_administrative.entity.do.seal_do import OaSeal
from sqlalchemy.sql import ColumnElement
from module_administrative.entity.vo.seal_vo import OaSealBaseModel, \
    OaSealPageQueryModel, OaSealDetail
from common.vo import PageModel, CrudResponseModel
from datetime import datetime
from module_basicdata.dao.public.flow_cate_dao import FlowCateDao

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.camel_converter import ResponseConverter


class SealService:
    time_fields = ['create_time', 'update_time', 'delete_time', 'check_time',
                   'use_time', 'start_time', 'end_time']
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaSealPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaSealBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await SealDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            return ResponseConverter.convert_page_result(query_list, cls.time_fields, 'OaSeal')
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaSealBaseModel) -> CrudResponseModel:
        if model.id:
            return await cls.update_service(query_db, model)

        try:
            model.create_time = int(datetime.now().timestamp())
            model.status = 1
            change = await SealDao.add(query_db, model)
            # await cls.add_record(query_db, change, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaSealBaseModel) -> CrudResponseModel:
        try:
            model.update_time = int(datetime.now().timestamp())
            change = await SealDao.update(query_db, model)
            # await cls.add_record(query_db, change, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaSealBaseModel:
        try:
            detail = await SealDao.get_info_by_id(query_db, id)
            detail['info'] = ResponseConverter.convert_to_camel_and_format_time(detail['info'],cls.time_fields)
            detail['records'] = ResponseConverter.convert_to_camel_and_format_time_list(detail['records'],cls.time_fields)
            if not detail:
                raise ServiceException(message="未找到该数据")
            return detail
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            await SealDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def pass_seal(cls, db: AsyncSession, data: OaSealBaseModel, userId: int):
        try:
            data.check_time = int(datetime.now().timestamp())
            await SealDao.pass_change(db, data)
            seal = await SealDao.get_info_by_id(db, data.id)
            await cls.add_record(db, seal, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='审核通过成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def reject_seal(cls, db: AsyncSession, data: OaSealBaseModel, userId: int):
        try:
            data.check_time = int(datetime.now().timestamp())
            await SealDao.reject_change(db, data)
            seal = await SealDao.get_info_by_id(db, data.id)
            await cls.add_record(db, seal, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='审核拒绝成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def cancel_seal(cls, db: AsyncSession, data: OaSealBaseModel, userId: int):
        try:
            await SealDao.cancel_change(db, data)
            seal = await SealDao.get_info_by_id(db, data.id)
            await cls.add_record(db, seal, data, userId)
            await db.commit()
            return CrudResponseModel(is_success=True, message='撤销申请成功')
        except Exception as e:
            await db.rollback()
            raise e
    @classmethod
    async def add_record(cls, db: AsyncSession, change: OaFlowRecordBaseModel, model: OaSealBaseModel, userId: int):
        try:
            flow_cate = await FlowCateDao.get_flow_cate_info(db, change.check_flow_id)
            step = await OaFlowStepDao.get_info_by_flow_id(db, change.check_flow_id)
            record = OaFlowRecordBaseModel()
            record.action_id = change.id
            record.check_table = flow_cate.check_table
            record.flow_id = change.check_flow_id
            record.check_files = model.file_ids
            record.check_uid = userId
            record.check_status = model.check_status
            record.step_id = step.id if step is not None else 0
            record.content = model.content
            record.check_time = int(datetime.now().timestamp())
            await FlowRecordDao.add(db, record)
        except Exception as e:
            await db.rollback()
            raise e