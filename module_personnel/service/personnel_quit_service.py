from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from common.constant import CommonConstant
from exceptions.exception import ServiceException
from module_basicdata.dao.public.flow_step_dao import OaFlowStepDao
from module_personnel.dao.flow_record_dao import FlowRecordDao
from module_personnel.dao.personnel_quit_dao import PersonnelQuitDao
from module_personnel.entity.do.personnel_quit_do import OaPersonalQuit
from sqlalchemy.sql import ColumnElement
from module_personnel.entity.vo.personnel_quit_vo import OaPersonalQuitBaseModel, \
    OaPersonnelQuitPageQueryModel, OaPersonnelQuitDetailModel
from common.vo import PageModel, CrudResponseModel
from datetime import datetime
from module_basicdata.dao.public.flow_cate_dao import FlowCateDao

from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.camel_converter import ModelConverter


class PersonnelQuitService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: OaPersonnelQuitPageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaPersonalQuitBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await PersonnelQuitDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaPersonalQuitBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
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
            change = await PersonnelQuitDao.add(query_db, model)
            model.remark = "提交离职申请"
            await cls.add_record(query_db, change, model)
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

            info = await PersonnelQuitDao.get_info_by_id(query_db, id)
            records = await FlowRecordDao.get_records_by_action_id(query_db, info.id, info.check_flow_id)
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
            quit = await PersonnelQuitDao.del_by_id(db, id)
            if quit.check_status != 0 or quit.check_status != 4:
                raise CrudResponseModel(is_success=False, message='请先撤销申请再删除')
            await PersonnelQuitDao.del_by_id(db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def review(cls, db: AsyncSession, data: OaPersonalQuitBaseModel):
        try:
            data.check_time = int(datetime.now().timestamp())
            change = await PersonnelQuitDao.review(db, data)
            await cls.add_record(db, change, data)
            await db.commit()
            return CrudResponseModel(is_success=True, message='操作成功！')
        except Exception as e:
            await db.rollback()
            raise e
            return CrudResponseModel(is_success=True, message='操作成功！')

    @classmethod
    async def add_record(cls, db: AsyncSession, change: OaFlowRecordBaseModel, model: OaPersonalQuitBaseModel):
        try:
            flow_cate = await FlowCateDao.get_flow_cate_info(db, change.check_flow_id)
            step = await OaFlowStepDao.get_info_by_flow_id(db, change.check_flow_id)
            record = OaFlowRecordBaseModel()
            record.action_id = change.id
            record.check_table = flow_cate.name
            record.flow_id = change.check_flow_id
            record.check_files = model.file_ids
            record.check_uid = change.check_last_uid
            record.check_status = model.check_status
            record.step_id = step.id if step is not None else 0
            record.content = model.remark
            record.check_time = int(datetime.now().timestamp())
            await FlowRecordDao.add(db, record)
        except Exception as e:
            await db.rollback()
            raise e