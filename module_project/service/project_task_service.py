from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_project.dao.project_task_dao import ProjectTaskDao
from module_project.entity.do.project_task_do import OaProjectTask
from module_project.entity.vo.project_task_vo import (
    AddProjectTaskModel,
    DeleteProjectTaskModel,
    EditProjectTaskModel,
    ProjectTaskModel,
    ProjectTaskPageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class ProjectTaskService:
    """
    项目任务管理服务层
    """

    @classmethod
    async def check_task_title_unique_services(cls, query_db: AsyncSession, page_object: ProjectTaskModel) -> bool:
        """
        校验任务主题是否唯一 service

        :param query_db: orm 对象
        :param page_object: 任务对象
        :return: 校验结果
        """
        # 获取 title 和 project_id，处理可能的 None 值
        title = page_object.title if page_object.title else ''
        project_id = page_object.project_id if page_object.project_id else 0
        
        # 如果 title 或 project_id 为空，跳过验重
        if not title.strip() or project_id == 0:
            logger.warning(f'跳过验重 - title: {title}, project_id: {project_id}')
            return True
        
        # 获取 id（编辑时需要排除自身）
        exclude_id = None
        if hasattr(page_object, 'id') and page_object.id and page_object.id > 0:
            exclude_id = page_object.id
        
        logger.info(f'开始任务验重 - title: "{title}", project_id: {project_id}, exclude_id: {exclude_id}')
        
        # 调用 DAO 层验重方法
        is_unique = await ProjectTaskDao.check_task_title_unique(
            query_db, title.strip(), project_id, exclude_id
        )
        
        logger.info(f'任务验重结果：{"通过" if is_unique else "失败"}')
        
        return is_unique

    @classmethod
    async def add_project_task_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddProjectTaskModel
    ) -> CrudResponseModel:
        """
        添加任务信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 任务对象
        :return: 添加结果
        """
        # 验重：检查任务主题在同一项目下是否已存在
        logger.info(f'=== 新增任务开始验重 ===')
        logger.info(f'传入数据 - title: {page_object.title}, project_id: {page_object.project_id}')
        
        is_unique = await cls.check_task_title_unique_services(query_db, page_object)
        
        if not is_unique:
            logger.error('验重失败：任务主题已存在')
            raise ServiceException(message=f'新增任务失败，该主题在项目下已存在')
        
        logger.info('验重通过，开始保存数据')
        
        try:
            current_time = int(datetime.now().timestamp())

            # 如果状态为已完成，设置完成时间和完成率
            if page_object.status == 3:
                page_object.over_time = current_time
                page_object.done_ratio = 100

            # 如果没有设置完成率，默认设置为 10
            if page_object.done_ratio is None or page_object.done_ratio == 0:
                page_object.done_ratio = 10

            page_object.create_time = current_time

            await ProjectTaskDao.add_project_task_dao(query_db, page_object)
            await query_db.commit()

            logger.info('新增任务成功')
            return CrudResponseModel(is_success=True, message='新增成功')
        except ServiceException:
            # 业务异常不需要 rollback
            raise
        except Exception as e:
            logger.error(f'新增任务异常：{str(e)}')
            await query_db.rollback()
            raise e

    @classmethod
    async def get_project_task_list_services(
            cls, query_db: AsyncSession, query_object: ProjectTaskPageQueryModel,
            current_user_id: int, auth_dids: str = '', son_dids: str = '',
            is_admin: bool = False, is_project_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取任务列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param current_user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为超级管理员
        :param is_project_admin: 是否为项目管理员
        :param is_page: 是否开启分页
        :return: 任务列表信息对象
        """
        task_list_result = await ProjectTaskDao.get_project_task_list(
            query_db, query_object, current_user_id, auth_dids, son_dids, is_admin, is_project_admin, is_page
        )

        # 转换为字典列表并添加扩展字段
        if isinstance(task_list_result, PageModel):
            task_list = []
            for item in task_list_result.rows:
                # 将 item 转换为字典（它可能已经是字典，或者是 ORM 对象）
                if isinstance(item, dict):
                    task_dict = item.copy()
                elif hasattr(item, '__dict__'):
                    # SQLAlchemy ORM 对象
                    task_dict = {key: value for key, value in item.__dict__.items() if not key.startswith('_')}
                else:
                    # 其他情况，尝试使用 model_dump 或直接转换
                    try:
                        task_dict = item.model_dump() if hasattr(item, 'model_dump') else dict(item)
                    except Exception:
                        task_dict = {}

                # 获取扩展字段
                task_id = task_dict.get('id') or task_dict.get('task_id')
                if task_id:
                    detail_info = await ProjectTaskDao.get_project_task_detail_by_id(query_db, task_id)
                    if detail_info:
                        # 添加扩展字段（这些字段在 ProjectTaskModel 中已定义）
                        task_dict['project_name'] = detail_info.get('project_name')
                        task_dict['admin_name'] = detail_info.get('admin_name')
                        task_dict['director_name'] = detail_info.get('director_name')
                        task_dict['dept_name'] = detail_info.get('dept_name')
                        task_dict['priority_name'] = detail_info.get('priority_name')
                        task_dict['status_name'] = detail_info.get('status_name')
                        task_dict['work_name'] = detail_info.get('work_name')
                        task_dict['end_time_str'] = detail_info.get('end_time_str')
                        task_dict['create_time_str'] = detail_info.get('create_time_str')
                        task_dict['update_time_str'] = detail_info.get('update_time_str')
                        task_dict['over_time_str'] = detail_info.get('over_time_str')

                task_list.append(task_dict)

            task_list_result.rows = CamelCaseUtil.transform_result(task_list)
        else:
            task_list = []
            for item in task_list_result:
                # 将 item 转换为字典
                if isinstance(item, dict):
                    task_dict = item.copy()
                elif hasattr(item, '__dict__'):
                    # SQLAlchemy ORM 对象
                    task_dict = {key: value for key, value in item.__dict__.items() if not key.startswith('_')}
                else:
                    # 其他情况
                    try:
                        task_dict = item.model_dump() if hasattr(item, 'model_dump') else dict(item)
                    except Exception:
                        task_dict = {}

                # 获取扩展字段
                task_id = task_dict.get('id') or task_dict.get('task_id')
                if task_id:
                    detail_info = await ProjectTaskDao.get_project_task_detail_by_id(query_db, task_id)
                    if detail_info:
                        # 添加扩展字段
                        task_dict['project_name'] = detail_info.get('project_name')
                        task_dict['admin_name'] = detail_info.get('admin_name')
                        task_dict['director_name'] = detail_info.get('director_name')
                        task_dict['dept_name'] = detail_info.get('dept_name')
                        task_dict['priority_name'] = detail_info.get('priority_name')
                        task_dict['status_name'] = detail_info.get('status_name')
                        task_dict['work_name'] = detail_info.get('work_name')
                        task_dict['end_time_str'] = detail_info.get('end_time_str')
                        task_dict['create_time_str'] = detail_info.get('create_time_str')
                        task_dict['update_time_str'] = detail_info.get('update_time_str')
                        task_dict['over_time_str'] = detail_info.get('over_time_str')

                task_list.append(task_dict)

            task_list_result = CamelCaseUtil.transform_result(task_list)

        return task_list_result

    @classmethod
    async def edit_project_task_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditProjectTaskModel
    ) -> CrudResponseModel:
        """
        编辑任务信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 任务对象
        :return: 编辑结果
        """
        if page_object.id:
            # 检查任务是否存在
            existing_task = await ProjectTaskDao.get_project_task_detail_by_id(query_db, page_object.id)
            if not existing_task:
                raise ServiceException(message='任务不存在')

            # 验重：检查任务主题在同一项目下是否已存在（排除自身）
            logger.info(f'=== 编辑任务开始验重 ===')
            logger.info(f'传入数据 - id: {page_object.id}, title: {page_object.title}, project_id: {page_object.project_id}')
            
            is_unique = await cls.check_task_title_unique_services(query_db, page_object)
            
            if not is_unique:
                logger.error('验重失败：任务主题已存在')
                raise ServiceException(message=f'编辑任务失败，该主题在项目下已存在')
            
            logger.info('验重通过，开始更新数据')

            try:
                current_time = int(datetime.now().timestamp())

                # 如果状态为已完成，设置完成时间和完成率
                if page_object.status == 3:
                    page_object.over_time = current_time
                    page_object.done_ratio = 100
                else:
                    page_object.over_time = 0

                page_object.update_time = current_time

                # 转换为字典，排除 None 值
                task_data = page_object.model_dump(exclude_unset=True, exclude_none=True)

                await ProjectTaskDao.edit_project_task_dao(query_db, page_object.id, task_data)
                await query_db.commit()

                logger.info('编辑任务成功')
                return CrudResponseModel(is_success=True, message='更新成功')
            except ServiceException:
                # 业务异常不需要 rollback
                raise
            except Exception as e:
                logger.error(f'编辑任务异常：{str(e)}')
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入任务 id 为空')

    @classmethod
    async def delete_project_task_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteProjectTaskModel
    ) -> CrudResponseModel:
        """
        删除任务信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 任务对象
        :return: 删除结果
        """
        if page_object.id:
            try:
                # 检查任务是否存在
                task_info = await ProjectTaskDao.get_project_task_detail_by_id(query_db, page_object.id)
                if not task_info:
                    raise ServiceException(message='任务不存在')

                await ProjectTaskDao.delete_project_task_dao(query_db, page_object.id)
                await query_db.commit()
                
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入任务 id 为空')

    @classmethod
    async def project_task_detail_services(cls, query_db: AsyncSession, id: int) -> dict[str, Any]:
        """
        获取任务详细信息 service - 直接返回字典
        """
        task_result = await ProjectTaskDao.get_project_task_detail_by_id(query_db, id)

        if not task_result:
            raise ServiceException(message="任务不存在")

        logger.info(f"【Service层】任务详情数据：{task_result}")

        return task_result
