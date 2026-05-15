from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from common.constant import CommonConstant
from common.vo import PageModel, CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.dao.dept_dao import DeptDao
from module_admin.dao.user_dao import UserDao
from module_basicdata.dao.public.flow_dao import OaFlowDao
from module_basicdata.dao.public.flow_step_dao import OaFlowStepDao
from module_basicdata.entity.do.public.flow_step_do import OaFlowStep
from module_basicdata.entity.vo.public.flow_vo import OaFlowBaseModel, OaFlowVOModel, OaFlowPageQueryModel
from datetime import datetime

from utils.camel_converter import ModelConverter


class FlowService:
    @classmethod
    async def get_flow_detail(cls, query_db: AsyncSession, id: int) -> OaFlowBaseModel:
        try:
            flow_cate_info = await OaFlowDao.get_flow_detail(query_db, id)
            if not flow_cate_info:
                raise ServiceException(message="未找到该数据")
            return flow_cate_info
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def update_flow(cls, query_db: AsyncSession, model: OaFlowBaseModel) -> CrudResponseModel:
        if not await cls.check_name_unique_services(query_db, model):
            raise ServiceException(message=f'修改失败，流程已存在')
        try:
            model.update_time = int(datetime.now().timestamp())
            result = await OaFlowDao.update_flow(query_db, model)
            if result:
                return CrudResponseModel(is_success=True, message='更新成功')
            return CrudResponseModel(is_success=False, message='更新失败')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def add_flow(cls, query_db: AsyncSession, model: OaFlowBaseModel) -> CrudResponseModel:
        if not await cls.check_name_unique_services(query_db, model):
            raise ServiceException(message=f'新增失败，流程已存在')
        try:
            model.create_time = int(datetime.now().timestamp())
            result = await OaFlowDao.add_flow(query_db, model)
            if result:
                return CrudResponseModel(is_success=True, message='新增成功')
            raise ServiceException(message='新增失败')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message='新增失败')

    @classmethod
    async def change_status_flow(cls,query_db: AsyncSession, model: OaFlowBaseModel) -> CrudResponseModel:
        try:
            result = await OaFlowDao.change_status_flow(query_db, model)
            if result:
                return CrudResponseModel(is_success=True, message='编辑成功')
            raise ServiceException(message='编辑失败')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message='编辑失败')

    @classmethod
    async def get_flow_list(cls,query_db: AsyncSession, model: OaFlowPageQueryModel, data_scope_sql: ColumnElement, is_page: bool) -> PageModel[OaFlowBaseModel]:
        try:
            result =  await OaFlowDao.get_flow_list(query_db, model, data_scope_sql, is_page)
            new_rows = []
            for flow,flowCate,flowModule in result.rows:
                if model.by_dept and flow['departmentIds'] != '':
                    """
                    开启部门过滤后，过滤掉非本部门的流程
                    """
                    dept_ids = flow['departmentIds'].split(',')
                    if str(model.dept_id) not in dept_ids:
                        result.total -= 1
                        continue
                flowVO = OaFlowVOModel(**flow)
                flowVO.cate_name = flowCate.get('title')
                flowVO.module_name = flowModule.get('title')
                flowVO.check_table = flowCate.get('checkTable')
                if flowVO.copy_uids != '':
                    copy_names = await UserDao.get_nick_name_by_user_id(query_db, [int(id) for id in flowVO.copy_uids.split(',')])
                    copy_names = ','.join(copy_names)
                    flowVO.copy_names = copy_names
                else:
                    flowVO.copy_names = '无'
                if flowVO.department_ids is None or flowVO.department_ids == '':
                    flowVO.department_names = '全公司'
                else:
                    dept_names = await DeptDao.get_dept_name(query_db, flowVO.department_ids.split(','))
                    if dept_names:
                        flowVO.department_names = ','.join([name['dept_name'] for name in dept_names])
                    else:
                        flowVO.department_names = '未找到部门'
                new_rows.append(flowVO)
            new_rows = ModelConverter.convert_to_camel_case(new_rows)
            result.rows = new_rows
            return result
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def check_name_unique_services(cls, query_db: AsyncSession, page_object: OaFlowBaseModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        title = -1 if page_object.title is None else page_object.title
        model = await OaFlowDao.get_info_by_title(query_db, OaFlowBaseModel(title=page_object.title))
        if model and model.id == page_object.id:
            return CommonConstant.UNIQUE
        if model and model.title == title:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE