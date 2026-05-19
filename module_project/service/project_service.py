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
    ) -> dict | list[dict[str, Any]]:
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

        # 格式化时间字段
        if isinstance(project_list_result, dict) and 'rows' in project_list_result:
            # 分页结果
            formatted_rows = []
            for row in project_list_result['rows']:
                if isinstance(row, dict):
                    formatted_row = cls._format_time_fields(row)
                    formatted_rows.append(formatted_row)
                else:
                    formatted_rows.append(row)
            project_list_result['rows'] = formatted_rows
        elif isinstance(project_list_result, list):
            # 非分页结果
            formatted_list = []
            for item in project_list_result:
                if isinstance(item, dict):
                    formatted_item = cls._format_time_fields(item)
                    formatted_list.append(formatted_item)
                else:
                    formatted_list.append(item)
            project_list_result = formatted_list

        return project_list_result

    @classmethod
    def _format_time_fields(cls, data: dict) -> dict:
        """
        格式化字典中的时间字段

        :param data: 原始字典
        :return: 格式化后的字典
        """
        formatted = data.copy()

        # 需要格式化的时间字段列表
        time_fields = ['start_time', 'end_time', 'create_time', 'update_time', 'delete_time']

        for field in time_fields:
            if field in formatted:
                value = formatted[field]
                # 如果值为 None、0 或空，设置为空字符串
                if value is None or value == 0:
                    formatted[field] = ''
                else:
                    # 格式化时间戳为日期时间字符串
                    formatted[field] = timestamp_to_datetime(value, '%Y-%m-%d %H:%M:%S')

        return formatted

    @classmethod
    def _clean_none_values(cls, data: dict) -> dict:
        """
        清理字典中的 None 值，替换为默认值

        :param data: 原始字典
        :return: 清理后的字典
        """
        cleaned = {}
        for key, value in data.items():
            if value is None:
                # 根据字段类型设置默认值
                if key in ['start_time', 'end_time', 'create_time', 'update_time', 'delete_time']:
                    cleaned[key] = 0  # 时间字段默认为 0，序列化器会转换为空字符串
                elif key in ['tasks_total', 'tasks_finish', 'tasks_unfinish', 'delay']:
                    cleaned[key] = 0  # 数字字段默认为 0
                elif key in ['status_name', 'admin_name', 'director_name', 'department', 'dept_name',
                            'cate', 'cate_title', 'range_time', 'step_director', 'step', 'tasks_pensent']:
                    cleaned[key] = ''  # 字符串字段默认为空字符串
                else:
                    cleaned[key] = None  # 其他字段保持 None
            else:
                cleaned[key] = value
        return cleaned

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

            start_time = page_object.start_time if page_object.start_time is not None else 0
            end_time = page_object.end_time if page_object.end_time is not None else 0

            if isinstance(start_time, str):
                from datetime import datetime as dt
                try:
                    start_time = int(dt.strptime(start_time, '%Y-%m-%d %H:%M:%S').timestamp())
                except (ValueError, TypeError):
                    start_time = 0

            if isinstance(end_time, str):
                from datetime import datetime as dt
                try:
                    end_time = int(dt.strptime(end_time, '%Y-%m-%d %H:%M:%S').timestamp())
                except (ValueError, TypeError):
                    end_time = 0

            # 处理 customer_id：支持整数或逗号分隔的字符串（用于项目成员）
            customer_id_value = ''
            if page_object.customer_id is not None:
                if isinstance(page_object.customer_id, int):
                    customer_id_value = str(page_object.customer_id)
                elif isinstance(page_object.customer_id, str):
                    customer_id_value = page_object.customer_id

            project_data = {
                'name': page_object.name if page_object.name is not None else '',
                'code': page_object.code if page_object.code is not None else '',
                'amount': page_object.amount if page_object.amount is not None else 0.00,
                'cate_id': page_object.cate_id if page_object.cate_id is not None else 0,
                'customer_id': 0,  # 项目表的 customer_id 固定为 0，成员信息存储在 oa_project_user 表
                'contract_id': page_object.contract_id if page_object.contract_id is not None else 0,
                'admin_id': page_object.admin_id,
                'director_uid': page_object.director_uid if page_object.director_uid is not None else 0,
                'did': page_object.did if page_object.did is not None else 0,
                'start_time': start_time,
                'end_time': end_time,
                'status': page_object.status if page_object.status is not None else 2,
                'content': page_object.content if page_object.content is not None else '',
                'create_time': current_time,
                'update_time': current_time,
                'delete_time': 0,
            }

            project = await ProjectDao.add_project_dao(query_db, project_data)

            # 处理项目阶段
            if hasattr(page_object, 'stages') and page_object.stages:
                await cls._save_project_stages(query_db, project.id, page_object.stages, current_time)

            # 处理项目成员（从 customer_id 字段获取成员ID列表）
            if hasattr(page_object, 'customer_id') and page_object.customer_id:
                await cls._save_project_users(query_db, project.id, page_object.customer_id, page_object.admin_id, current_time)

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
            if not await cls.check_project_name_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改项目失败，项目名称已存在')

            try:
                valid_fields = {c.name for c in OaProject.__table__.columns}
                exclude_fields = {'id', 'create_time', 'delete_time', 'admin_id', 'customer_id'}

                edit_project = {
                    k: v for k, v in page_object.model_dump(exclude_unset=True).items()
                    if k in valid_fields and k not in exclude_fields
                }

                # 处理时间字段：将字符串日期转换为时间戳
                from datetime import datetime as dt
                for field in ['start_time', 'end_time']:
                    if field in edit_project and isinstance(edit_project[field], str):
                        try:
                            edit_project[field] = int(dt.strptime(edit_project[field], '%Y-%m-%d %H:%M:%S').timestamp())
                        except (ValueError, TypeError):
                            edit_project[field] = 0

                project_info = await ProjectDao.get_project_detail_by_id(query_db, page_object.id)
                if project_info and project_info.get('project_info'):
                    edit_project['update_time'] = int(datetime.now().timestamp())
                    await ProjectDao.edit_project_dao(query_db, page_object.id, edit_project)

                    if hasattr(page_object, 'stages') and page_object.stages is not None:
                        current_time = int(datetime.now().timestamp())
                        await cls._update_project_stages(query_db, page_object.id, page_object.stages, current_time)

                    # 处理项目成员（从 customer_id 字段获取成员ID列表）
                    if hasattr(page_object, 'customer_id') and page_object.customer_id is not None:
                        current_time = int(datetime.now().timestamp())
                        await cls._update_project_users(query_db, page_object.id, page_object.customer_id, page_object.admin_id, current_time)

                    await query_db.commit()
                    return CrudResponseModel(is_success=True, message='更新成功')
                else:
                    raise ServiceException(message='项目不存在')

            except Exception as e:
                await query_db.rollback()
                raise e

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
        try:
            project_info = await ProjectDao.get_project_detail_by_id(query_db, page_object.id)
            if project_info and project_info.get('project_info'):
                await ProjectDao.delete_project_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            else:
                raise ServiceException(message='项目不存在')

        except Exception as e:
            await query_db.rollback()
            raise e

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
        
        # 将下划线格式的字段名转换为驼峰格式
        project_info_dict = {}
        for key, value in project_info.__dict__.items():
            if key != '_sa_instance_state':
                # 下划线转驼峰
                parts = key.split('_')
                camel_key = parts[0] + ''.join(part.capitalize() for part in parts[1:])
                project_info_dict[camel_key] = value
        
        # 添加扩展字段
        for key in ['cate_title', 'customer_name', 'contract_name', 'admin_name', 'director_name', 'dept_name', 'status_name']:
            if key in project_dict:
                # 下划线转驼峰
                parts = key.split('_')
                camel_key = parts[0] + ''.join(part.capitalize() for part in parts[1:])
                project_info_dict[camel_key] = project_dict[key]
        
        result_dict = project_info_dict

        # 获取项目阶段
        stages = await ProjectStepDao.get_steps_by_project_id(query_db, project_id)
        if stages:
            stage_list = []
            for stage in stages:
                stage_dict = stage.__dict__.copy()
                stage_dict.pop('_sa_instance_state', None)
                
                # 查询阶段负责人姓名
                if stage.director_uid and stage.director_uid > 0:
                    from module_admin.dao.user_dao import UserDao
                    director_result = await UserDao.get_user_by_id(query_db, stage.director_uid)
                    if director_result and director_result.get('user_basic_info'):
                        director_info = director_result['user_basic_info']
                        stage_dict['director_name'] = director_info.nick_name or director_info.user_name
                
                # 查询阶段成员姓名列表
                if stage.uids:
                    from module_admin.dao.user_dao import UserDao
                    uid_list = [int(uid.strip()) for uid in stage.uids.split(',') if uid.strip() and uid.strip().isdigit()]
                    member_names = []
                    for uid in uid_list:
                        member_result = await UserDao.get_user_by_id(query_db, uid)
                        if member_result and member_result.get('user_basic_info'):
                            member_info = member_result['user_basic_info']
                            member_names.append(member_info.nick_name or member_info.user_name)
                    stage_dict['member_names'] = member_names
                
                stage_list.append(ProjectStepModel(**stage_dict))
            result_dict['stages'] = stage_list

        # 获取项目成员列表
        from module_contract.dao.project_user_dao import ProjectUserDao
        project_users = await ProjectUserDao.get_users_by_project_id(query_db, project_id)
        if project_users:
            from module_admin.dao.user_dao import UserDao
            member_ids = [user.uid for user in project_users]
            member_names = []
            for uid in member_ids:
                member_result = await UserDao.get_user_by_id(query_db, uid)
                if member_result and member_result.get('user_basic_info'):
                    member_info = member_result['user_basic_info']
                    member_names.append(member_info.nick_name or member_info.user_name)
            
            # 将成员ID和名称都保存到结果中
            result_dict['customerId'] = ','.join([str(uid) for uid in member_ids])
            result_dict['customerNames'] = ','.join(member_names)

        result = ProjectModel(**result_dict)

        return result

    @classmethod
    async def _save_project_stages(
            cls, query_db: AsyncSession, project_id: int, stages: list[ProjectStepModel], current_time: int
    ) -> None:
        """
        保存项目阶段

        :param query_db: orm 对象
        :param project_id: 项目 ID
        :param stages: 项目阶段列表
        :param current_time: 当前时间戳
        :return: None
        """
        for stage in stages:
            stage_data = {
                'project_id': project_id,
                'title': stage.title,
                'start_time': stage.start_time,
                'end_time': stage.end_time,
                'remark': stage.remark,
                'create_time': current_time,
                'update_time': current_time,
                'delete_time': 0,
            }
            await ProjectStepDao.add_step(query_db, stage_data)

    @classmethod
    async def _save_project_users(
            cls, query_db: AsyncSession, project_id: int, customer_id: str, admin_id: int, current_time: int
    ) -> None:
        """
        保存项目成员

        :param query_db: orm 对象
        :param project_id: 项目 ID
        :param customer_id: 客户 ID（逗号分隔的成员ID字符串）
        :param admin_id: 管理员 ID
        :param current_time: 当前时间戳
        :return: None
        """
        from module_contract.dao.project_user_dao import ProjectUserDao
        
        # 解析成员ID列表
        if customer_id:
            uid_list = [int(uid.strip()) for uid in customer_id.split(',') if uid.strip().isdigit()]
            
            # 批量新增成员
            users_list = []
            for uid in uid_list:
                users_list.append({
                    'uid': uid,
                    'project_id': project_id,
                    'admin_id': admin_id,
                    'create_time': current_time,
                    'delete_time': 0,
                })
            
            if users_list:
                await ProjectUserDao.batch_add_users(query_db, users_list)

    @classmethod
    async def _update_project_stages(
            cls, query_db: AsyncSession, project_id: int, stages: list[ProjectStepModel], current_time: int
    ) -> None:
        """
        更新项目阶段

        :param query_db: orm 对象
        :param project_id: 项目 ID
        :param stages: 项目阶段列表
        :param current_time: 当前时间戳
        :return: None
        """
        for stage in stages:
            stage_data = {
                'title': stage.title,
                'start_time': stage.start_time,
                'end_time': stage.end_time,
                'remark': stage.remark,
                'update_time': current_time,
            }
            await ProjectStepDao.update_step(query_db, stage.id, stage_data)

    @classmethod
    async def _update_project_users(
            cls, query_db: AsyncSession, project_id: int, customer_id: str, admin_id: int, current_time: int
    ) -> None:
        """
        更新项目成员

        :param query_db: orm 对象
        :param project_id: 项目 ID
        :param customer_id: 客户 ID（逗号分隔的成员ID字符串）
        :param admin_id: 管理员 ID
        :param current_time: 当前时间戳
        :return: None
        """
        from module_contract.dao.project_user_dao import ProjectUserDao
        
        # 先逻辑删除所有现有成员
        await ProjectUserDao.delete_users_by_project_id(query_db, project_id, current_time)
        
        # 解析新的成员ID列表
        if customer_id:
            uid_list = [int(uid.strip()) for uid in customer_id.split(',') if uid.strip().isdigit()]
            
            # 批量新增成员
            users_list = []
            for uid in uid_list:
                users_list.append({
                    'uid': uid,
                    'project_id': project_id,
                    'admin_id': admin_id,
                    'create_time': current_time,
                    'delete_time': 0,
                })
            
            if users_list:
                await ProjectUserDao.batch_add_users(query_db, users_list)