from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql.coercions import cls

from common.constant import CommonConstant
from common.vo import PageModel, CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.dao.dept_dao import DeptDao
from module_basicdata.dao.public.flow_dao import OaFlowDao
from module_basicdata.entity.vo.public.flow_vo import OaFlowBaseModel, OaFlowVOModel
from datetime import datetime

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
            raise ServiceException(message=f'新增失败，工具已存在')
        try:
            model.create_time = int(datetime.now().timestamp())
            result = await OaFlowDao.add_flow(query_db, model)
            if result:
                return CrudResponseModel(is_success=True, message='新增成功')
            return CrudResponseModel(is_success=False, message='新增失败')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def change_status_flow(cls,query_db: AsyncSession, model: OaFlowBaseModel) -> CrudResponseModel:
        try:
            result = await OaFlowDao.change_status_flow(query_db, model)
            if result:
                return CrudResponseModel(is_success=True, message='更新成功')
            return CrudResponseModel(is_success=False, message='更新失败', data=False)
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def get_flow_list(cls,query_db: AsyncSession, model: OaFlowBaseModel, data_scope_sql: ColumnElement, is_page: bool) -> PageModel[OaFlowBaseModel]:
        try:
            result =  await OaFlowDao.get_flow_list(query_db, model, data_scope_sql, is_page)
            new_rows = []
            for flow,flowCate,flowModule,user in result.rows:
                flowVO = OaFlowVOModel(**flow)
                flowVO.cate_name = flowCate.get('title')
                flowVO.module_name = flowModule.get('title')
                if flowVO.copy_names:
                    flowVO.copy_names = user.get('nickName')
                else:
                    flowVO.copy_names = '无'
                if flowVO.department_ids is None or flowVO.department_ids == '':
                    flowVO.department_names = '全公司'
                else:
                    dept_names = await DeptDao.get_name_list_ids(query_db, flowVO.department_ids)
                    if dept_names:
                        for dept_name in dept_names:
                            flowVO.department_names = ''.join(dept_name)
                    else:
                        flowVO.department_names = '未找到部门'
                new_rows.append(flowVO)
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