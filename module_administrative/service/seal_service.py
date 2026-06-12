from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_basicdata.dao.public.flow_step_dao import OaFlowStepDao
from module_administrative.dao.seal_dao import SealDao
from module_personnel.dao.file_dao import FileDAO
from module_personnel.dao.flow_record_dao import FlowRecordDao
from sqlalchemy.sql import ColumnElement
from module_administrative.entity.vo.seal_vo import OaSealBaseModel, \
    OaSealPageQueryModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime
from module_basicdata.dao.public.flow_cate_dao import FlowCateDao

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.camel_converter import ResponseConverter, ModelConverter
from utils.timeformat import int_time


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
            if model.use_time:
                model.use_time = int_time(model.use_time)
            if model.start_time:
                model.start_time = int_time(model.start_time)
            elif model.start_time == '':
                model.start_time = None
            if model.end_time:
                model.end_time = int_time(model.end_time)
            elif model.end_time == '':
                model.end_time = None
            if model.is_borrow == 0:
                model.start_time = 0
                model.end_time = 0
            await SealDao.add(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message="新增失败")
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaSealBaseModel) -> CrudResponseModel:
        try:
            model.update_time = int(datetime.now().timestamp())
            if model.use_time:
                model.use_time = int_time(model.use_time)
            if model.start_time:
                model.start_time = int_time(model.start_time)
            if model.end_time:
                model.end_time = int_time(model.end_time)
            if model.is_borrow == 0:
                model.start_time = 0
                model.end_time = 0
            await SealDao.update(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='编辑成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message="编辑失败")
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int):
        try:
            detail = await SealDao.get_info_by_id(query_db, id)
            if not detail:
                raise ServiceException(message="未找到该数据")

            detail = ResponseConverter.convert_to_camel_and_format_time(detail,cls.time_fields)
            detail['records'] = ResponseConverter.convert_to_camel_and_format_time_list(detail['records'],cls.time_fields)
            if detail['fileIds'] != '' and detail['fileIds'] is not None:
                file_ids = detail['fileIds'].split(',')
            else:
                file_ids = []
            attachments = await FileDAO.get_files(query_db,file_ids)
            file_list = []
            for attachment in attachments:
                file_list.append(ModelConverter.convert_to_camel_case(dict(attachment)))
            detail['attachments'] = file_list
            return detail
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message="获取失败")
        pass

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            seal = await SealDao.get_info_by_id(db, id)
            if seal['check_status'] == 0 or seal['check_status'] == 4:    # 只能删除未提交审核或已撤销的申请
                await SealDao.del_by_id(db, id)
            else:
                raise ServiceException(message='请先撤销申请再删除')
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise ServiceException(message="删除失败")

    @classmethod
    async def return_seal_service(cls, query_db: AsyncSession, seal_id: int) -> CrudResponseModel:
        """
        还章服务方法

        :param query_db: orm对象
        :param seal_id: 用章申请ID
        :return: 操作结果
        """
        try:
            seal_info = await SealDao.get_info_by_id(query_db, seal_id)
            if not seal_info:
                raise ServiceException(message='未找到该用章申请')
            if seal_info.get('check_status') != 2:
                raise ServiceException(message='该申请未审批通过，无法还章')
            if seal_info.get('seal_status') != 1:
                raise ServiceException(message='该印章当前不在使用中')

            await SealDao.return_seal(query_db, seal_id)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='还章成功')
        except ServiceException:
            raise
        except Exception as e:
            await query_db.rollback()
            import traceback
            logger.error(f"还章失败：{traceback.format_exc()}")
            raise ServiceException(message=f"还章失败：{str(e)}")