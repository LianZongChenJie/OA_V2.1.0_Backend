from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_administrative.dao.leaves_dao import LeavesDao
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.do.dept_do import SysDept
from module_administrative.entity.vo.leaves_vo import (
    AddLeavesModel,
    DeleteLeavesModel,
    EditLeavesModel,
    LeavesModel,
    LeavesPageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class LeavesService:
    """
    请假管理模块服务层
    """

    @classmethod
    async def get_leaves_list_services(
            cls, query_db: AsyncSession, query_object: LeavesPageQueryModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取请假列表信息 service

        :param query_db: orm 对象
        :param query_object: 分页查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 请假列表信息对象
        """
        leaves_list_result = await LeavesDao.get_leaves_list(query_db, query_object, user_id, is_page)

        leaves_list_result = CamelCaseUtil.transform_result(leaves_list_result)

        if is_page and hasattr(leaves_list_result, 'rows') and leaves_list_result.rows:
            formatted_rows = await cls._format_leaves_list(leaves_list_result.rows, query_db)
            leaves_list_result.rows = formatted_rows
        elif not is_page and leaves_list_result:
            leaves_list_result = await cls._format_leaves_list(leaves_list_result, query_db)

        return leaves_list_result

    @classmethod
    async def _format_leaves_list(cls, leaves_list: list[dict[str, Any]], query_db: AsyncSession) -> list[dict[str, Any]]:
        """
        格式化请假列表数据
        """
        if not leaves_list:
            return leaves_list
        
        types_map = {1: '事假', 2: '年假', 3: '调休假', 4: '病假', 5: '婚假', 6: '丧假', 7: '产假', 8: '陪产假', 9: '其他'}
        
        for item in leaves_list:
            if not isinstance(item, dict):
                continue
            
            types_val = item.get('types')
            if types_val:
                item['typesStr'] = types_map.get(types_val, '')
            else:
                item['typesStr'] = ''
            
            create_time = item.get('createTime')
            if create_time and isinstance(create_time, (int, float)) and create_time > 0:
                try:
                    if create_time > 1e12:
                        create_time_seconds = create_time / 1000
                    else:
                        create_time_seconds = create_time
                    item['createTime'] = datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    logger.error(f"创建时间格式化失败: {e}")
                    item['createTime'] = ''
            else:
                item['createTime'] = ''
            
            start_date = item.get('startDate')
            if start_date and isinstance(start_date, (int, float)) and start_date > 0:
                try:
                    if start_date > 1e12:
                        start_date_seconds = start_date / 1000
                    else:
                        start_date_seconds = start_date
                    item['startDate'] = datetime.fromtimestamp(start_date_seconds).strftime('%Y-%m-%d')
                except Exception as e:
                    logger.error(f"开始时间格式化失败: {e}")
                    item['startDate'] = ''
            else:
                item['startDate'] = ''
            
            end_date = item.get('endDate')
            if end_date and isinstance(end_date, (int, float)) and end_date > 0:
                try:
                    if end_date > 1e12:
                        end_date_seconds = end_date / 1000
                    else:
                        end_date_seconds = end_date
                    item['endDate'] = datetime.fromtimestamp(end_date_seconds).strftime('%Y-%m-%d')
                except Exception as e:
                    logger.error(f"结束时间格式化失败: {e}")
                    item['endDate'] = ''
            else:
                item['endDate'] = ''
            
            admin_id = item.get('adminId')
            if admin_id and isinstance(admin_id, int) and admin_id > 0:
                try:
                    admin_user = await query_db.execute(
                        select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id == admin_id)
                    )
                    user_info = admin_user.first()
                    if user_info:
                        item['adminName'] = user_info.nick_name or user_info.user_name
                    else:
                        item['adminName'] = ''
                except Exception as e:
                    logger.error(f"查询创建人失败: {e}")
                    item['adminName'] = ''
            else:
                item['adminName'] = ''
            
            did = item.get('did')
            if did and isinstance(did, int) and did > 0:
                try:
                    dept = await query_db.execute(
                        select(SysDept.dept_name).where(SysDept.dept_id == did)
                    )
                    dept_info = dept.scalar_one_or_none()
                    item['deptName'] = dept_info if dept_info else ''
                except Exception as e:
                    logger.error(f"查询部门失败: {e}")
                    item['deptName'] = ''
            else:
                item['deptName'] = ''
        
        return leaves_list

    @classmethod
    async def add_leaves_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddLeavesModel, user_id: int, dept_id: int
    ) -> CrudResponseModel:
        """
        新增请假信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增请假对象
        :param user_id: 当前用户 ID
        :param dept_id: 当前用户部门 ID
        :return: 新增请假校验结果
        """
        if not user_id or user_id <= 0:
            raise ServiceException(message='当前用户信息异常，请重新登录')
        
        try:
            current_time = int(datetime.now().timestamp())
            
            leaves_dict = {
                'types': page_object.types,
                'start_date': page_object.start_date if page_object.start_date else 0,
                'end_date': page_object.end_date if page_object.end_date else 0,
                'start_span': page_object.start_span if page_object.start_span is not None else 0,
                'end_span': page_object.end_span if page_object.end_span is not None else 0,
                'duration': page_object.duration if page_object.duration is not None else 0.0,
                'reason': page_object.reason,
                'file_ids': page_object.file_ids if page_object.file_ids is not None else '',
                'admin_id': user_id,
                'did': dept_id if dept_id else 0,
                'create_time': current_time,
                'update_time': current_time,
                'delete_time': 0,
                'check_status': 0,
                'check_flow_id': 0,
                'check_step_sort': 0,
                'check_uids': '',
                'check_last_uid': '',
                'check_history_uids': '',
                'check_copy_uids': '',
                'check_time': 0
            }

            logger.info(f"准备插入请假数据: admin_id={leaves_dict['admin_id']}, did={leaves_dict['did']}, types={leaves_dict.get('types')}, duration={leaves_dict.get('duration')}, reason={leaves_dict.get('reason')}")

            await LeavesDao.add_leaves_dao(query_db, leaves_dict)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f"新增请假失败: {str(e)}", exc_info=True)
            raise e

    @classmethod
    async def edit_leaves_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditLeavesModel
    ) -> CrudResponseModel:
        """
        编辑请假信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑请假对象
        :return: 编辑请假校验结果
        """
        if page_object.id:
            try:
                edit_leaves = page_object.model_dump(
                    exclude_unset=True,
                    exclude={'id', 'types_str', 'admin_name', 'dept_name', 'create_time', 'delete_time'}
                )
                edit_leaves['update_time'] = int(datetime.now().timestamp())
                await LeavesDao.edit_leaves_dao(query_db, page_object.id, edit_leaves)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='请假不存在')

    @classmethod
    async def delete_leaves_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteLeavesModel
    ) -> CrudResponseModel:
        """
        删除请假信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除请假对象
        :return: 删除请假校验结果
        """
        if page_object.id:
            try:
                leaves = await LeavesDao.get_leaves_detail_by_id(query_db, page_object.id)
                if not leaves:
                    raise ServiceException(message='请假不存在')

                update_time = int(datetime.now().timestamp())
                await LeavesDao.delete_leaves_dao(
                    query_db,
                    LeavesModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入请假 id 为空')

    @classmethod
    async def leaves_detail_services(cls, query_db: AsyncSession, leaves_id: int) -> LeavesModel:
        """
        获取请假详细信息 service

        :param query_db: orm 对象
        :param leaves_id: 请假 id
        :return: 请假 id 对应的信息
        """
        leaves = await LeavesDao.get_leaves_detail_by_id(query_db, leaves_id)
        result = LeavesModel(**CamelCaseUtil.transform_result(leaves)) if leaves else LeavesModel()

        return result