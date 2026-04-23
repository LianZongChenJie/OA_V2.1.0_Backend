import decimal

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from exceptions.exception import ServiceException
from module_personnel.dao.labor_contract_dao import LaborContractDao
from sqlalchemy.sql import ColumnElement
from module_personnel.entity.vo.lable_contract_vo import OaLaborContractPageQueryModel, OaLaborContractBaseModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime

from utils.camel_converter import ModelConverter
from utils.timeformat import int_time


class LaborContractService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaLaborContractPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaLaborContractBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await LaborContractDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            row_list = []
            for row in query_list.rows:
                row = dict(row)
                row.update(row['OaLaborContract'].to_dict())
                row.pop('OaLaborContract')
                if row['cate'] == 1:
                    row['cate_name'] = '劳动合同'
                elif row['cate'] == 2:
                    row['cate_name'] = '劳务合同'
                elif row['cate'] == 3:
                    row['cate_name'] = '保密协议'
                if row['types'] == 1:
                    row['types_name'] = '新签合同'
                elif row['types'] == 2:
                    row['types_name'] = '续签合同'
                elif row['types'] == 3:
                    row['types_name'] = '变更合同'
                if row['status'] == 1:
                    row['status_name'] = '正常'
                elif row['status'] == 2:
                    row['status_name'] = '已到期'
                row_list.append(ModelConverter.convert_to_camel_case(row))
            query_list.rows = row_list
            result_list = query_list
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaLaborContractBaseModel) -> CrudResponseModel:
        try:
            model.create_time = int(datetime.now().timestamp())
            model.status = 1
            model.sign_time = int_time(model.sign_time)
            model.start_time = int_time(model.start_time)
            model.end_time = int_time(model.end_time)
            model.trial_end_time = int_time(model.trial_end_time)
            if model.trial_salary is None or model.trial_salary == '':
                model.trial_salary = decimal.Decimal(0)
            if model.worker_salary is None or model.worker_salary == '':
                model.worker_salary = decimal.Decimal(0)
            await LaborContractDao.add(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaLaborContractBaseModel) -> CrudResponseModel:
        try:
            model.update_time = int(datetime.now().timestamp())
            model.sign_time = int_time(model.sign_time)
            model.start_time = int_time(model.start_time)
            model.end_time = int_time(model.end_time)
            model.trial_end_time = int_time(model.trial_end_time)
            await LaborContractDao.update(query_db, model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass


    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaLaborContractBaseModel:
        try:
            info = await LaborContractDao.get_info_by_id(query_db, id)
            if not info:
                raise ServiceException(message="未找到该数据")
            return info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        try:
            await LaborContractDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e