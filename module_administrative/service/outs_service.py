from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_administrative.dao.outs_dao import OutsDao
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.do.dept_do import SysDept
from module_administrative.entity.vo.outs_vo import (
    AddOutsModel,
    DeleteOutsModel,
    EditOutsModel,
    OutsModel,
    OutsPageQueryModel,
)
from module_personnel.dao.flow_record_dao import FlowRecordDao
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class OutsService:
    """
    外出管理模块服务层
    """

    @classmethod
    async def get_outs_list_services(
            cls, query_db: AsyncSession, query_object: OutsPageQueryModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取外出列表信息 service

        :param query_db: orm 对象
        :param query_object: 分页查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 外出列表信息对象
        """
        outs_list_result = await OutsDao.get_outs_list(query_db, query_object, user_id, is_page)

        outs_list_result = CamelCaseUtil.transform_result(outs_list_result)

        if is_page and hasattr(outs_list_result, 'rows') and outs_list_result.rows:
            formatted_rows = await cls._format_outs_list(outs_list_result.rows, query_db)
            outs_list_result.rows = formatted_rows
        elif not is_page and outs_list_result:
            outs_list_result = await cls._format_outs_list(outs_list_result, query_db)

        return outs_list_result

    @classmethod
    async def _format_outs_list(cls, outs_list: list[dict[str, Any]], query_db: AsyncSession) -> list[dict[str, Any]]:
        """
        格式化外出列表数据
        """
        if not outs_list:
            return outs_list

        for item in outs_list:
            if not isinstance(item, dict):
                continue

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

        return outs_list

    @classmethod
    async def add_outs_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddOutsModel, user_id: int, dept_id: int
    ) -> CrudResponseModel:
        """
        新增外出信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增外出对象
        :param user_id: 当前用户 ID
        :param dept_id: 当前用户部门 ID
        :return: 新增外出校验结果
        """
        if not user_id or user_id <= 0:
            raise ServiceException(message='当前用户信息异常，请重新登录')

        try:
            current_time = int(datetime.now().timestamp())
            
            # 处理 start_date
            start_date_value = page_object.start_date
            if isinstance(start_date_value, str) and ('-' in start_date_value or ':' in start_date_value):
                try:
                    dt = datetime.fromisoformat(start_date_value)
                    start_date_value = int(dt.timestamp())
                except ValueError:
                    start_date_value = 0
            elif not start_date_value:
                start_date_value = 0
            
            # 处理 end_date
            end_date_value = page_object.end_date
            if isinstance(end_date_value, str) and ('-' in end_date_value or ':' in end_date_value):
                try:
                    dt = datetime.fromisoformat(end_date_value)
                    end_date_value = int(dt.timestamp())
                except ValueError:
                    end_date_value = 0
            elif not end_date_value:
                end_date_value = 0

            outs_dict = {
                'start_date': start_date_value,
                'end_date': end_date_value,
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

            logger.info(f"准备插入外出数据: admin_id={outs_dict['admin_id']}, did={outs_dict['did']}, duration={outs_dict.get('duration')}, reason={outs_dict.get('reason')}")

            await OutsDao.add_outs_dao(query_db, outs_dict)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f"新增外出失败: {str(e)}", exc_info=True)
            raise e

    @classmethod
    async def edit_outs_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditOutsModel
    ) -> CrudResponseModel:
        """
        编辑外出信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑外出对象
        :return: 编辑外出校验结果
        """
        if page_object.id:
            try:
                edit_outs = page_object.model_dump(
                    exclude_unset=True,
                    exclude={'id', 'admin_name', 'dept_name', 'create_time', 'delete_time'}
                )
                
                # 处理 start_date
                start_date_value = edit_outs.get('start_date')
                if isinstance(start_date_value, str) and ('-' in start_date_value or ':' in start_date_value):
                    try:
                        dt = datetime.fromisoformat(start_date_value)
                        edit_outs['start_date'] = int(dt.timestamp())
                    except ValueError:
                        edit_outs['start_date'] = 0
                elif not start_date_value:
                    edit_outs['start_date'] = 0
                
                # 处理 end_date
                end_date_value = edit_outs.get('end_date')
                if isinstance(end_date_value, str) and ('-' in end_date_value or ':' in end_date_value):
                    try:
                        dt = datetime.fromisoformat(end_date_value)
                        edit_outs['end_date'] = int(dt.timestamp())
                    except ValueError:
                        edit_outs['end_date'] = 0
                elif not end_date_value:
                    edit_outs['end_date'] = 0
                
                edit_outs['update_time'] = int(datetime.now().timestamp())
                await OutsDao.edit_outs_dao(query_db, page_object.id, edit_outs)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='外出不存在')

    @classmethod
    async def delete_outs_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteOutsModel
    ) -> CrudResponseModel:
        """
        删除外出信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除外出对象
        :return: 删除外出校验结果
        """
        if page_object.id:
            try:
                outs = await OutsDao.get_outs_detail_by_id(query_db, page_object.id)
                if not outs:
                    raise ServiceException(message='外出不存在')

                update_time = int(datetime.now().timestamp())
                await OutsDao.delete_outs_dao(
                    query_db,
                    OutsModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入外出 id 为空')

    @classmethod
    async def outs_detail_services(cls, query_db: AsyncSession, outs_id: int) -> OutsModel:
        """
        获取外出详细信息 service

        :param query_db: orm 对象
        :param outs_id: 外出 id
        :return: 外出 id 对应的信息
        """
        outs = await OutsDao.get_outs_detail_by_id(query_db, outs_id)
        if not outs:
            return OutsModel()
        
        result_dict = CamelCaseUtil.transform_result(outs)
        
        # 格式化创建时间
        create_time = result_dict.get('createTime')
        if create_time and isinstance(create_time, (int, float)) and create_time > 0:
            if create_time > 1e12:
                create_time_seconds = create_time / 1000
            else:
                create_time_seconds = create_time
            result_dict['createTime'] = datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
        else:
            result_dict['createTime'] = ''
        
        # 格式化开始日期
        start_date = result_dict.get('startDate')
        if start_date and isinstance(start_date, (int, float)) and start_date > 0:
            if start_date > 1e12:
                start_date_seconds = start_date / 1000
            else:
                start_date_seconds = start_date
            result_dict['startDate'] = datetime.fromtimestamp(start_date_seconds).strftime('%Y-%m-%d %H:%M:%S')
        else:
            result_dict['startDate'] = ''
        
        # 格式化结束日期
        end_date = result_dict.get('endDate')
        if end_date and isinstance(end_date, (int, float)) and end_date > 0:
            if end_date > 1e12:
                end_date_seconds = end_date / 1000
            else:
                end_date_seconds = end_date
            result_dict['endDate'] = datetime.fromtimestamp(end_date_seconds).strftime('%Y-%m-%d %H:%M:%S')
        else:
            result_dict['endDate'] = ''
        
        # 获取创建人姓名
        admin_id = result_dict.get('adminId')
        if admin_id and isinstance(admin_id, int) and admin_id > 0:
            try:
                admin_user = await query_db.execute(
                    select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id == admin_id)
                )
                user_info = admin_user.first()
                if user_info:
                    result_dict['adminName'] = user_info.nick_name or user_info.user_name
                else:
                    result_dict['adminName'] = ''
            except Exception as e:
                logger.error(f"查询创建人失败: {e}")
                result_dict['adminName'] = ''
        else:
            result_dict['adminName'] = ''
        
        # 获取部门名称
        did = result_dict.get('did')
        if did and isinstance(did, int) and did > 0:
            try:
                dept = await query_db.execute(
                    select(SysDept.dept_name).where(SysDept.dept_id == did)
                )
                dept_info = dept.scalar_one_or_none()
                result_dict['deptName'] = dept_info if dept_info else ''
            except Exception as e:
                logger.error(f"查询部门失败: {e}")
                result_dict['deptName'] = ''
        else:
            result_dict['deptName'] = ''
        
        # 获取审批记录
        flow_id = result_dict.get('checkFlowId')
        if flow_id and isinstance(flow_id, int) and flow_id > 0:
            try:
                records = await FlowRecordDao.get_records_dict(db=query_db, action_id=outs_id, flow_id=flow_id)
                # 将字段名转换为驼峰格式
                if records:
                    records = CamelCaseUtil.transform_result(records)
                result_dict['records'] = records if records else []
            except Exception as e:
                logger.error(f"查询审批记录失败: {e}")
                result_dict['records'] = []
        else:
            result_dict['records'] = []
        
        result = OutsModel(**result_dict)
        return result