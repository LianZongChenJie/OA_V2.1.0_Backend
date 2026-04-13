from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_home.entity.vo.approve_vo import ApprovePageQueryModel


class ApproveDao:
    """
    统一审批管理模块数据库操作层
    """

    @classmethod
    async def get_approve_unified_list(
            cls, db: AsyncSession, query_object: ApprovePageQueryModel, where_clause: str, user_id: int, is_page: bool = True
    ) -> dict[str, Any]:
        """
        获取统一审批列表

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param where_clause: WHERE 条件子句
        :param user_id: 用户ID
        :param is_page: 是否分页
        :return: 审批列表数据
        """
        # 定义需要查询的审批表（使用正确的表名）
        approve_tables = [
            {'table': 'oa_leaves', 'name': '请假', 'type_field': None},
            {'table': 'oa_overtimes', 'name': '加班', 'type_field': None},
            {'table': 'oa_trips', 'name': '出差', 'type_field': None},
            {'table': 'oa_outs', 'name': '外出', 'type_field': None},
            {'table': 'oa_seal', 'name': '用章', 'type_field': None},
            {'table': 'oa_official_docs', 'name': '公文', 'type_field': None},
            {'table': 'oa_meeting_order', 'name': '会议', 'type_field': None},
            {'table': 'oa_expense', 'name': '报销', 'type_field': None},
            {'table': 'oa_invoice', 'name': '开票', 'type_field': 'invoice_type'},
            {'table': 'oa_ticket', 'name': '收票', 'type_field': 'invoice_type'},
            {'table': 'oa_contract', 'name': '合同', 'type_field': None},
            {'table': 'oa_purchase', 'name': '采购', 'type_field': None},
        ]

        sql_parts = []
        count_sql_parts = []

        for table_info in approve_tables:
            table_name = table_info['table']
            check_name = table_info['name']
            type_field = table_info['type_field']

            # 检查表是否存在
            check_table_sql = f"SHOW TABLES LIKE '{table_name}'"
            table_exists = await db.execute(text(check_table_sql))
            if not table_exists.scalar():
                continue

            # 构建 SELECT 语句
            if type_field:
                select_sql = f"""
                    SELECT 
                        id, admin_id, did, create_time, check_status, check_flow_id, 
                        check_step_sort, check_uids, check_last_uid, check_history_uids, 
                        check_copy_uids, check_time, 
                        '{table_name}' as table_name, 
                        '{check_name}' as check_name, 
                        {type_field} as invoice_type, 
                        '{check_name}' as types
                    FROM {table_name}
                """
            else:
                select_sql = f"""
                    SELECT 
                        id, admin_id, did, create_time, check_status, check_flow_id, 
                        check_step_sort, check_uids, check_last_uid, check_history_uids, 
                        check_copy_uids, check_time, 
                        '{table_name}' as table_name, 
                        '{check_name}' as check_name, 
                        '{check_name}' as invoice_type, 
                        '{check_name}' as types
                    FROM {table_name}
                """

            where_condition = f"WHERE delete_time = 0 AND {where_clause}"
            sql_parts.append(f"{select_sql} {where_condition}")
            count_sql_parts.append(f"SELECT COUNT(*) as count FROM {table_name} WHERE delete_time = 0 AND {where_clause}")

        # 如果没有有效的表，返回空结果
        if not sql_parts:
            return {
                'data': [],
                'total': 0,
                'page': query_object.page if is_page else 1,
                'limit': query_object.limit if is_page else 0,
            }

        # 合并 SQL
        union_sql = " UNION ALL ".join(sql_parts)
        order_by = " ORDER BY create_time DESC"
        
        # 计算总数
        count_union_sql = " UNION ALL ".join(count_sql_parts)
        total_count_sql = f"SELECT SUM(count) as total FROM ({count_union_sql}) as counts"
        total_result = await db.execute(text(total_count_sql))
        total_row = total_result.first()
        total_count = total_row.total if total_row and total_row.total else 0

        # 分页
        if is_page:
            page = query_object.page
            page_size = query_object.limit
            offset = (page - 1) * page_size
            final_sql = f"{union_sql}{order_by} LIMIT {page_size} OFFSET {offset}"
        else:
            final_sql = f"{union_sql}{order_by}"

        # 执行查询
        result = await db.execute(text(final_sql))
        rows = result.fetchall()

        # 转换为字典列表
        data_list = []
        for row in rows:
            data_list.append({
                'id': row.id,
                'admin_id': row.admin_id,
                'did': row.did,
                'create_time': row.create_time,
                'check_status': row.check_status,
                'check_flow_id': row.check_flow_id,
                'check_step_sort': row.check_step_sort,
                'check_uids': row.check_uids,
                'check_last_uid': row.check_last_uid,
                'check_history_uids': row.check_history_uids,
                'check_copy_uids': row.check_copy_uids,
                'check_time': row.check_time,
                'table_name': row.table_name,
                'check_name': row.check_name,
                'invoice_type': row.invoice_type,
                'types': row.types,
            })

        return {
            'data': data_list,
            'total': total_count,
            'page': query_object.page if is_page else 1,
            'limit': query_object.limit if is_page else total_count,
        }