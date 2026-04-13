from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.do.dept_do import SysDept
from module_home.dao.approve_dao import ApproveDao
from module_home.entity.vo.approve_vo import ApprovePageQueryModel


class ApproveService:
    """
    统一审批管理服务层
    """

    @classmethod
    async def _format_approve_list(cls, data_list: list[dict[str, Any]], query_db: AsyncSession) -> list[dict[str, Any]]:
        """
        格式化审批列表数据

        :param data_list: 原始数据列表
        :param query_db: 数据库会话
        :return: 格式化后的列表
        """
        if not data_list:
            return data_list

        check_status_map = {
            0: '待审核',
            1: '审核中',
            2: '审核通过',
            3: '审核不通过',
            4: '撤销审核'
        }

        for item in data_list:
            # 格式化时间
            create_time = item.get('create_time')
            if create_time and isinstance(create_time, (int, float)) and create_time > 0:
                try:
                    if create_time > 1e12:
                        create_time_seconds = create_time / 1000
                    else:
                        create_time_seconds = create_time
                    item['create_time'] = datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    item['create_time'] = ''
            else:
                item['create_time'] = ''

            # 获取创建人姓名
            admin_id = item.get('admin_id')
            if admin_id:
                try:
                    user_result = await query_db.execute(
                        select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id == admin_id)
                    )
                    user_info = user_result.first()
                    if user_info:
                        item['admin_name'] = user_info.nick_name or user_info.user_name
                    else:
                        item['admin_name'] = ''
                except Exception:
                    item['admin_name'] = ''
            else:
                item['admin_name'] = ''

            # 获取部门名称
            did = item.get('did')
            if did:
                try:
                    dept_result = await query_db.execute(
                        select(SysDept.dept_name).where(SysDept.dept_id == did)
                    )
                    dept_info = dept_result.scalar_one_or_none()
                    item['department'] = dept_info if dept_info else ''
                except Exception:
                    item['department'] = ''
            else:
                item['department'] = ''

            # 审核状态字符串
            check_status = item.get('check_status')
            item['check_status_str'] = check_status_map.get(check_status, '')

            # 当前审批人
            check_status_val = item.get('check_status')
            check_uids = item.get('check_uids')
            if check_status_val == 1 and check_uids:
                try:
                    uid_list = [int(uid.strip()) for uid in check_uids.split(',') if uid.strip().isdigit()]
                    if uid_list:
                        users_result = await query_db.execute(
                            select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id.in_(uid_list))
                        )
                        users = users_result.all()
                        item['check_users'] = ','.join([u.nick_name or u.user_name for u in users])
                    else:
                        item['check_users'] = '-'
                except Exception:
                    item['check_users'] = '-'
            else:
                item['check_users'] = '-'

            # 抄送人
            check_copy_uids = item.get('check_copy_uids')
            if check_copy_uids:
                try:
                    copy_uid_list = [int(uid.strip()) for uid in check_copy_uids.split(',') if uid.strip().isdigit()]
                    if copy_uid_list:
                        copy_users_result = await query_db.execute(
                            select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id.in_(copy_uid_list))
                        )
                        copy_users = copy_users_result.all()
                        item['check_copy_users'] = ','.join([u.nick_name or u.user_name for u in copy_users])
                    else:
                        item['check_copy_users'] = '-'
                except Exception:
                    item['check_copy_users'] = '-'
            else:
                item['check_copy_users'] = '-'

            # 设置类型名称和URL（简化版，实际应该从流程配置表获取）
            table_name = item.get('table_name', '')
            invoice_type = item.get('invoice_type', '')

            # 根据表名和发票类型确定实际的类型名称
            if table_name in ['invoice', 'ticket']:
                if invoice_type == 0:
                    actual_type = f"{table_name}_a"
                else:
                    actual_type = table_name
            elif table_name == 'approve':
                types = item.get('types', '')
                actual_type = f"approve_{types}"
            else:
                actual_type = table_name

            item['types_name'] = item.get('check_name', '')
            item['view_url'] = f"/{actual_type}/view/{{id}}"
            item['add_url'] = f"/{actual_type}/add"

        return data_list

    @classmethod
    async def get_my_approve_list_services(
            cls, query_db: AsyncSession, query_object: ApprovePageQueryModel, user_id: int
    ) -> dict[str, Any]:
        """
        获取我申请的审批列表

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 用户ID
        :return: 审批列表
        """
        status = query_object.status
        where_clause = f"admin_id = {user_id}"

        if status == 1:
            where_clause += " AND check_status < 2"
        elif status == 2:
            where_clause += " AND check_status = 2"
        elif status == 3:
            where_clause += " AND check_status > 2"

        result = await ApproveDao.get_approve_unified_list(query_db, query_object, where_clause, user_id, True)

        # 格式化数据
        if result['data']:
            result['data'] = await cls._format_approve_list(result['data'], query_db)

        return result

    @classmethod
    async def get_check_approve_list_services(
            cls, query_db: AsyncSession, query_object: ApprovePageQueryModel, user_id: int
    ) -> dict[str, Any]:
        """
        获取待我审核/我已审核的审批列表

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 用户ID
        :return: 审批列表
        """
        status = query_object.status

        if status == 0:
            # 待我审核或我已审核
            where_clause = f"(FIND_IN_SET('{user_id}', check_uids) OR FIND_IN_SET('{user_id}', check_history_uids))"
        elif status == 1:
            # 待我审核
            where_clause = f"FIND_IN_SET('{user_id}', check_uids)"
        elif status == 2:
            # 我已审核
            where_clause = f"FIND_IN_SET('{user_id}', check_history_uids)"
        else:
            where_clause = f"(FIND_IN_SET('{user_id}', check_uids) OR FIND_IN_SET('{user_id}', check_history_uids))"

        result = await ApproveDao.get_approve_unified_list(query_db, query_object, where_clause, user_id, True)

        # 格式化数据
        if result['data']:
            result['data'] = await cls._format_approve_list(result['data'], query_db)

        return result

    @classmethod
    async def get_copy_approve_list_services(
            cls, query_db: AsyncSession, query_object: ApprovePageQueryModel, user_id: int
    ) -> dict[str, Any]:
        """
        获取抄送给我的审批列表

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 用户ID
        :return: 审批列表
        """
        status = query_object.status
        where_clause = f"FIND_IN_SET('{user_id}', check_copy_uids) > 0"

        if status == 1:
            where_clause += " AND check_status < 2"
        elif status == 2:
            where_clause += " AND check_status = 2"
        elif status == 3:
            where_clause += " AND check_status > 2"

        result = await ApproveDao.get_approve_unified_list(query_db, query_object, where_clause, user_id, True)

        # 格式化数据
        if result['data']:
            result['data'] = await cls._format_approve_list(result['data'], query_db)

        return result