from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_project.dao.project_dao import ProjectDao
from module_project.dao.project_step_dao import ProjectStepDao
from module_project.entity.do.project_do import OaProject
from module_project.entity.vo.project_vo import (
    AddProjectModel,
    DeleteProjectModel,
    EditProjectModel,
    ProjectModel,
    ProjectPageQueryModel,
    ProjectStepModel,
)
from utils.common_util import CamelCaseUtil
from utils.time_format_util import timestamp_to_datetime


class ProjectService:
    """
    项目管理服务层
    """

    @classmethod
    async def get_project_list_services(
            cls, query_db: AsyncSession, query_object: ProjectPageQueryModel,
            current_user_id: int, auth_dids: str = '', son_dids: str = '',
            is_admin: bool = False, is_project_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取项目列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param current_user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为超级管理员
        :param is_project_admin: 是否为项目管理员
        :param is_page: 是否开启分页
        :return: 项目列表信息对象
        """
        # 如果是项目管理员，不进行权限过滤
        if is_project_admin:
            project_list_result = await ProjectDao.get_project_list(
                query_db, query_object, current_user_id, '', '', True, True, is_page
            )
        else:
            project_list_result = await ProjectDao.get_project_list(
                query_db, query_object, current_user_id, auth_dids, son_dids, is_admin, is_project_admin, is_page
            )

        return project_list_result

    @classmethod
    async def check_project_name_unique_services(
            cls, query_db: AsyncSession, page_object: ProjectModel
    ) -> bool:
        """
        校验项目名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 项目对象
        :return: 校验结果
        """
        project_id = -1 if page_object.id is None else page_object.id
        project = await ProjectDao.get_project_detail_by_info(query_db, page_object)
        if project and project.id != project_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_project_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddProjectModel
    ) -> CrudResponseModel:
        """
        新增项目信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增项目对象
        :return: 新增项目校验结果
        """
        try:
            # 校验项目名称是否唯一
            if not await cls.check_project_name_unique_services(query_db, page_object):
                raise ServiceException(message=f'新增项目失败，项目名称已存在')

            current_time = int(datetime.now().timestamp())

            # 只提取数据库表存在的字段
            project_data = {
                'code': page_object.code if page_object.code is not None else '',
                'name': page_object.name,
                'amount': page_object.amount if page_object.amount is not None else 0.00,
                'cate_id': page_object.cate_id if page_object.cate_id is not None else 0,
                'customer_id': page_object.customer_id if page_object.customer_id is not None else 0,
                'contract_id': page_object.contract_id if page_object.contract_id is not None else 0,
                'admin_id': page_object.admin_id,
                'director_uid': page_object.director_uid if page_object.director_uid is not None else 0,
                'did': page_object.did if page_object.did is not None else 0,
                'start_time': page_object.start_time if page_object.start_time is not None else 0,
                'end_time': page_object.end_time if page_object.end_time is not None else 0,
                'status': page_object.status if page_object.status is not None else 2,  # 默认为进行中
                'content': page_object.content if page_object.content is not None else '',
                'create_time': current_time,
                'update_time': current_time,
                'delete_time': 0,
            }

            project = await ProjectDao.add_project_dao(query_db, project_data)

            # 处理项目阶段
            if hasattr(page_object, 'stages') and page_object.stages:
                await cls._save_project_stages(query_db, project.id, page_object.stages, current_time)

            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_project_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditProjectModel
    ) -> CrudResponseModel:
        """
        编辑项目信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑项目对象
        :return: 编辑项目校验结果
        """
        if page_object.id:
            # 校验项目名称是否唯一（排除自身）
            if not await cls.check_project_name_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改项目失败，项目名称已存在')

            try:
                # 只提取数据库表存在的字段，排除不需要更新的字段
                valid_fields = {c.name for c in OaProject.__table__.columns}
                exclude_fields = {'id', 'create_time', 'delete_time', 'admin_id'}

                edit_project = {
                    k: v for k, v in page_object.model_dump(exclude_unset=True).items()
                    if k in valid_fields and k not in exclude_fields
                }

                project_info = await cls.project_detail_services(query_db, page_object.id)

                if project_info and project_info.id:
                    edit_project['update_time'] = int(datetime.now().timestamp())
                    await ProjectDao.edit_project_dao(query_db, page_object.id, edit_project)

                    # 处理项目阶段
                    if hasattr(page_object, 'stages') and page_object.stages is not None:
                        current_time = int(datetime.now().timestamp())
                        await cls._update_project_stages(query_db, page_object.id, page_object.stages, current_time)

                    await query_db.commit()
                    return CrudResponseModel(is_success=True, message='更新成功')
                else:
                    raise ServiceException(message='项目不存在')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='项目不存在')

    @classmethod
    async def delete_project_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteProjectModel
    ) -> CrudResponseModel:
        """
        删除项目信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除项目对象
        :return: 删除项目校验结果
        """
        if page_object.id:
            try:
                project_info = await cls.project_detail_services(query_db, page_object.id)
                if not project_info or not project_info.id:
                    raise ServiceException(message='项目不存在')

                update_time = int(datetime.now().timestamp())
                await ProjectDao.delete_project_dao(
                    query_db,
                    ProjectModel(id=page_object.id, update_time=update_time)
                )

                # 删除项目阶段
                await ProjectStepDao.delete_steps_by_project_id(query_db, page_object.id)

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入项目 id 为空')

    @classmethod
    async def project_detail_services(cls, query_db: AsyncSession, project_id: int) -> ProjectModel:
        """
        获取项目详细信息 service

        :param query_db: orm 对象
        :param project_id: 项目 ID
        :return: 项目 ID 对应的信息
        """
        project_dict = await ProjectDao.get_project_detail_by_id(query_db, project_id)

        if not project_dict:
            return ProjectModel()

        # 合并项目信息和扩展字段
        project_info = project_dict['project_info']
        result_dict = {**project_info.__dict__, **project_dict}
        result_dict.pop('_sa_instance_state', None)

        # 获取项目阶段
        stages = await ProjectStepDao.get_steps_by_project_id(query_db, project_id)
        if stages:
            stage_list = []
            for step in stages:
                step_dict = step.__dict__.copy()
                step_dict.pop('_sa_instance_state', None)
                
                # 获取阶段负责人姓名
                if step_dict.get('director_uid') and step_dict['director_uid'] > 0:
                    from module_admin.dao.user_dao import UserDao
                    director_result = await UserDao.get_user_by_id(query_db, step_dict['director_uid'])
                    if director_result and director_result.get('user_basic_info'):
                        step_dict['director_name'] = director_result['user_basic_info'].nick_name
                
                # 获取阶段成员姓名
                if step_dict.get('uids'):
                    uid_list = [int(uid.strip()) for uid in step_dict['uids'].split(',') if uid.strip()]
                    if uid_list:
                        from module_admin.dao.user_dao import UserDao
                        member_names = []
                        for uid in uid_list:
                            user_result = await UserDao.get_user_by_id(query_db, uid)
                            if user_result and user_result.get('user_basic_info'):
                                member_names.append(user_result['user_basic_info'].nick_name)
                        step_dict['member_names'] = member_names
                
                stage_list.append(ProjectStepModel(**CamelCaseUtil.transform_result(step_dict)))
            
            result_dict['stages'] = stage_list

        return ProjectModel(**CamelCaseUtil.transform_result(result_dict))

    @classmethod
    async def _save_project_stages(cls, query_db: AsyncSession, project_id: int, stages: list, current_time: int):
        """
        保存项目阶段

        :param query_db: orm 对象
        :param project_id: 项目ID
        :param stages: 阶段列表
        :param current_time: 当前时间戳
        :return:
        """
        for index, stage_data in enumerate(stages):
            if isinstance(stage_data, dict):
                step_data = {
                    'project_id': project_id,
                    'title': stage_data.get('name') or stage_data.get('title', ''),
                    'director_uid': stage_data.get('directorUid', 0),
                    'uids': stage_data.get('memberUids') or stage_data.get('uids', ''),
                    'sort': stage_data.get('sort', index + 1),
                    'is_current': 1 if index == 0 else 0,
                    'start_time': stage_data.get('startTime', 0),
                    'end_time': stage_data.get('endTime', 0),
                    'remark': stage_data.get('remark', ''),
                    'create_time': current_time,
                    'update_time': current_time,
                    'delete_time': 0,
                }
            elif hasattr(stage_data, 'model_dump'):
                data_dict = stage_data.model_dump(by_alias=False)
                step_data = {
                    'project_id': project_id,
                    'title': data_dict.get('title') or data_dict.get('name', ''),
                    'director_uid': data_dict.get('director_uid', 0),
                    'uids': data_dict.get('uids') or data_dict.get('member_uids', ''),
                    'sort': data_dict.get('sort', index + 1),
                    'is_current': 1 if index == 0 else 0,
                    'start_time': data_dict.get('start_time', 0),
                    'end_time': data_dict.get('end_time', 0),
                    'remark': data_dict.get('remark', ''),
                    'create_time': current_time,
                    'update_time': current_time,
                    'delete_time': 0,
                }
            else:
                step_data = {
                    'project_id': project_id,
                    'title': getattr(stage_data, 'title', '') or getattr(stage_data, 'name', ''),
                    'director_uid': getattr(stage_data, 'director_uid', 0) or getattr(stage_data, 'directorUid', 0),
                    'uids': getattr(stage_data, 'uids', '') or getattr(stage_data, 'memberUids', '') or getattr(stage_data, 'member_uids', ''),
                    'sort': getattr(stage_data, 'sort', index + 1),
                    'is_current': 1 if index == 0 else 0,
                    'start_time': getattr(stage_data, 'start_time', 0) or getattr(stage_data, 'startTime', 0),
                    'end_time': getattr(stage_data, 'end_time', 0) or getattr(stage_data, 'endTime', 0),
                    'remark': getattr(stage_data, 'remark', ''),
                    'create_time': current_time,
                    'update_time': current_time,
                    'delete_time': 0,
                }

            await ProjectStepDao.add_step(query_db, step_data)

    @classmethod
    async def _update_project_stages(cls, query_db: AsyncSession, project_id: int, stages: list, current_time: int):
        """
        更新项目阶段

        :param query_db: orm 对象
        :param project_id: 项目ID
        :param stages: 阶段列表
        :param current_time: 当前时间戳
        :return:
        """
        # 先获取现有阶段
        existing_steps = await ProjectStepDao.get_steps_by_project_id(query_db, project_id)
        existing_step_ids = {step.id for step in existing_steps}

        # 收集提交的阶段ID
        submitted_step_ids = set()

        for index, stage_data in enumerate(stages):
            if isinstance(stage_data, dict):
                step_id = stage_data.get('id')
                step_data_dict = {
                    'title': stage_data.get('name') or stage_data.get('title', ''),
                    'director_uid': stage_data.get('directorUid', 0),
                    'uids': stage_data.get('memberUids') or stage_data.get('uids', ''),
                    'sort': stage_data.get('sort', index + 1),
                    'is_current': 1 if index == 0 else 0,
                    'start_time': stage_data.get('startTime', 0),
                    'end_time': stage_data.get('endTime', 0),
                    'remark': stage_data.get('remark', ''),
                    'update_time': current_time,
                }
            elif hasattr(stage_data, 'model_dump'):
                step_id = getattr(stage_data, 'id', None)
                data_dict = stage_data.model_dump(by_alias=False)
                step_data_dict = {
                    'title': data_dict.get('title') or data_dict.get('name', ''),
                    'director_uid': data_dict.get('director_uid', 0),
                    'uids': data_dict.get('uids') or data_dict.get('member_uids', ''),
                    'sort': data_dict.get('sort', index + 1),
                    'is_current': 1 if index == 0 else 0,
                    'start_time': data_dict.get('start_time', 0),
                    'end_time': data_dict.get('end_time', 0),
                    'remark': data_dict.get('remark', ''),
                    'update_time': current_time,
                }
            else:
                step_id = getattr(stage_data, 'id', None)
                step_data_dict = {
                    'title': getattr(stage_data, 'title', '') or getattr(stage_data, 'name', ''),
                    'director_uid': getattr(stage_data, 'director_uid', 0) or getattr(stage_data, 'directorUid', 0),
                    'uids': getattr(stage_data, 'uids', '') or getattr(stage_data, 'memberUids', '') or getattr(stage_data, 'member_uids', ''),
                    'sort': getattr(stage_data, 'sort', index + 1),
                    'is_current': 1 if index == 0 else 0,
                    'start_time': getattr(stage_data, 'start_time', 0) or getattr(stage_data, 'startTime', 0),
                    'end_time': getattr(stage_data, 'end_time', 0) or getattr(stage_data, 'endTime', 0),
                    'remark': getattr(stage_data, 'remark', ''),
                    'update_time': current_time,
                }

            if step_id and step_id in existing_step_ids:
                # 更新现有阶段
                await ProjectStepDao.update_step(query_db, step_id, step_data_dict)
                submitted_step_ids.add(step_id)
            else:
                # 新增阶段
                step_data_dict['project_id'] = project_id
                step_data_dict['create_time'] = current_time
                step_data_dict['delete_time'] = 0
                await ProjectStepDao.add_step(query_db, step_data_dict)

        # 删除不在提交列表中的阶段
        deleted_step_ids = existing_step_ids - submitted_step_ids
        for step_id in deleted_step_ids:
            await ProjectStepDao.delete_step(query_db, step_id)
