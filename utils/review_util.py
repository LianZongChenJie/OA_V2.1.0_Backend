from module_admin.entity.do.user_do import SysUser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.page_util import PageModel
from typing import Any


class ReviewUtil:
    @classmethod
    async def enrich_checker_names(cls, db: AsyncSession, info: dict) -> dict:
        """补充当前审批人和历史审批人名称"""

        # 当前审批人
        check_uids = info.get('check_uids')
        if check_uids:
            uids = [int(uid) for uid in check_uids.split(',') if uid]
            if uids:
                stmt = select(SysUser.user_id, SysUser.nick_name).where(
                    SysUser.user_id.in_(uids)
                )
                result = await db.execute(stmt)
                users = result.all()
                info['check_user_names'] = [u.nick_name for u in users]
                info['check_user_names_str'] = ','.join(info['check_user_names'])
            else:
                info['check_user_names'] = []
                info['check_user_names_str'] = ''
        else:
            info['check_user_names'] = []
            info['check_user_names_str'] = ''

        # 历史审批人
        check_history_uids = info.get('check_history_uids')
        if check_history_uids:
            uids = [int(uid) for uid in check_history_uids.split(',') if uid]
            if uids:
                stmt = select(SysUser.user_id, SysUser.nick_name).where(
                    SysUser.user_id.in_(uids)
                )
                result = await db.execute(stmt)
                users = result.all()
                info['check_history_names'] = [u.nick_name for u in users]
                info['check_history_names_str'] = ','.join(info['check_history_names'])
            else:
                info['check_history_names'] = []
                info['check_history_names_str'] = ''
        else:
            info['check_history_names'] = []
            info['check_history_names_str'] = ''

        return info

    @classmethod
    async def enrich_checker_names_for_rows(cls, tableName: str,  db: AsyncSession, page_list: PageModel | list[dict[str, Any]]):
        """
        补充当前审批人和历史审批人名称
        :param db:
        :param page_list:
        :param tableName:
        :return:
        """
        if page_list and hasattr(page_list, 'rows') and page_list.rows:
            all_uids = set()

            # 收集所有需要查询的 UIDs
            for row in page_list.rows:
                # 将 RowMapping 转换为字典以便读取
                row_dict = dict(row)
                dept_change = row_dict.get(tableName)

                if dept_change:
                    check_uids = getattr(dept_change, 'check_uids', '')
                    check_history_uids = getattr(dept_change, 'check_history_uids', '')
                else:
                    check_uids = row_dict.get('check_uids', '')
                    check_history_uids = row_dict.get('check_history_uids', '')

                if check_uids:
                    all_uids.update([int(uid) for uid in check_uids.split(',') if uid])
                if check_history_uids:
                    all_uids.update([int(uid) for uid in check_history_uids.split(',') if uid])

            # 批量查询用户名称
            user_map = {}
            if all_uids:
                user_stmt = select(SysUser.user_id, SysUser.nick_name).where(
                    SysUser.user_id.in_(all_uids)
                )
                user_result = await db.execute(user_stmt)
                for uid, name in user_result.all():
                    user_map[uid] = name

            # 创建新的行列表（普通字典）
            new_rows = []
            for row in page_list.rows:
                # 转换为普通字典
                new_row = dict(row)
                dept_change = new_row.get(tableName)

                if dept_change:
                    check_uids = getattr(dept_change, 'check_uids', '')
                    check_history_uids = getattr(dept_change, 'check_history_uids', '')
                else:
                    check_uids = new_row.get('check_uids', '')
                    check_history_uids = new_row.get('check_history_uids', '')

                # 当前审批人名称
                if check_uids:
                    uids = [int(uid) for uid in check_uids.split(',') if uid]
                    new_row['checkUserNames'] = [user_map.get(uid, '') for uid in uids]
                    new_row['checkUserNamesStr'] = ','.join(filter(None, new_row['checkUserNames']))
                else:
                    new_row['checkUserNames'] = []
                    new_row['checkUserNamesStr'] = ''

                # 历史审批人名称
                if check_history_uids:
                    uids = [int(uid) for uid in check_history_uids.split(',') if uid]
                    new_row['checkHistoryNames'] = [user_map.get(uid, '') for uid in uids]
                    new_row['checkHistoryNamesStr'] = ','.join(filter(None, new_row['checkHistoryNames']))
                else:
                    new_row['checkHistoryNames'] = []
                    new_row['checkHistoryNamesStr'] = ''

                new_rows.append(new_row)

            # 替换为修改后的字典列表
            page_list.rows = new_rows
            return page_list
        else:
            return page_list
