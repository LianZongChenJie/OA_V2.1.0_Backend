from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from common.constant import CommonConstant
from exceptions.exception import ServiceException
from module_personnel.dao.flow_record_dao import FlowRecordDao
from module_personnel.dao.personnel_quit_dao import PersonnelQuitDao
from sqlalchemy.sql import ColumnElement
from module_personnel.entity.vo.personnel_quit_vo import OaPersonalQuitBaseModel, \
    OaPersonnelQuitPageQueryModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime
from utils.camel_converter import ModelConverter
from utils.timeformat import int_time


class PersonnelQuitService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaPersonnelQuitPageQueryModel,
                                    data_scope_sql: ColumnElement, user_id: int, is_page: bool = False) -> PageModel[
                                                                                                 OaPersonalQuitBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await PersonnelQuitDao.get_page_list(query_db, query_object, data_scope_sql, user_id, is_page)
        if is_page:
            row_list = []
            for row in query_list.rows:
                row = dict(row)
                row.update(row['OaPersonalQuit'].to_dict())
                row.pop('OaPersonalQuit')
                if row['post_name'] is not None:
                    row['post_name'] = row['post_name'].strip(',')
                    row['post_name'] = row['post_name'].replace(',,', ',')
                if row['lead_name'] is not None:
                    row['lead_name'] = row['lead_name'].strip(',')
                    row['lead_name'] = row['lead_name'].replace(',,', ',')
                if row['rec_ji_names'] is not None:
                    row['rec_ji_names'] = row['rec_ji_names'].strip(',')
                    row['rec_ji_names'] = row['rec_ji_names'].replace(',,', ',')
                row_list.append(ModelConverter.convert_to_camel_case(row))
            query_list.rows = row_list
            return query_list
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaPersonalQuitBaseModel) -> CrudResponseModel:
        if model.id:
            return await cls.update_service(query_db, model)

        if not await cls.check_unique_services(query_db, model):
            raise ServiceException(message=f'新增审核{model.title}失败，该员工已有再审核流程不能重复提交')
        try:
            model.create_time = int(datetime.now().timestamp())
            model.status = 1
            model.quit_time = int_time(model.quit_time)
            await PersonnelQuitDao.add(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaPersonalQuitBaseModel) -> CrudResponseModel:
        try:
            model.update_time = int(datetime.now().timestamp())
            model.quit_time = int_time(model.quit_time)
            await PersonnelQuitDao.update(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaPersonalQuitBaseModel:
        try:

            info = await PersonnelQuitDao.get_info_dict(query_db, id)
            if not info:
                raise ServiceException(message="未找到该数据")
            info = dict(info)
            info.update(info['OaPersonalQuit'].to_dict())
            if info['post_name'] is not None:
                info['post_name'] = info['post_name'].strip(',')
                info['post_name'] = info['post_name'].replace(',,', ',')
            if info['lead_name'] is not None:
                info['lead_name'] = info['lead_name'].strip(',')
                info['lead_name'] = info['lead_name'].replace(',,', ',')
            if info['rec_ji_names'] is not None:
                info['rec_ji_names'] = info['rec_ji_names'].strip(',')
                info['rec_ji_names'] = info['rec_ji_names'].replace(',,', ',')
            info.pop('OaPersonalQuit')
            records = await FlowRecordDao.get_records_dict(query_db, info['id'], info['check_flow_id'])
            detail = {}
            detail.update(info)
            detail['records'] = records
            if not detail:
                raise ServiceException(message="未找到该数据")
            return ModelConverter.convert_to_camel_case(detail)
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def check_unique_services(cls, query_db: AsyncSession, page_object: OaPersonalQuitBaseModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        title = -1 if page_object.uid is None else page_object.uid
        model = await PersonnelQuitDao.get_info_by_uid(query_db, page_object)
        if model and model.id == page_object.id:
            return CommonConstant.UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            quit = await PersonnelQuitDao.get_info_by_id(db, id)
            if quit.check_status != 0 and quit.check_status != 4:
                raise CrudResponseModel(is_success=False, message='申请已经开始审核，请先撤销申请再删除')
            await PersonnelQuitDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e
