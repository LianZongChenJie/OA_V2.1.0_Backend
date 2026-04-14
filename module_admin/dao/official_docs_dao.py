from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.official_docs_do import OaOfficialDocs
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.vo.official_docs_vo import (
    OfficialDocsModel,
    OfficialDocsPageQueryModel,
    PendingOfficialDocsModel,
    ReviewedOfficialDocsModel,
)
from utils.page_util import PageUtil


class OfficialDocsDao:
    """
    公文管理模块数据库操作层
    """

    @classmethod
    async def get_official_docs_detail_by_info(cls, db: AsyncSession, docs_info: OfficialDocsModel) -> OaOfficialDocs | None:
        """
        根据公文主题或编号获取公文信息

        :param db: orm 对象
        :param docs_info: 公文对象
        :return: 公文信息
        """
        conditions = [OaOfficialDocs.delete_time == 0]
        
        if docs_info.title:
            conditions.append(OaOfficialDocs.title == docs_info.title)
        elif docs_info.code:
            conditions.append(OaOfficialDocs.code == docs_info.code)
        
        query = select(OaOfficialDocs).where(*conditions)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def get_official_docs_detail_by_id(cls, db: AsyncSession, docs_id: int) -> dict[str, Any] | None:
        """
        根据公文 id 获取公文详细信息

        :param db: orm 对象
        :param docs_id: 公文 id
        :return: 公文详细信息对象
        """
        query = select(OaOfficialDocs).where(OaOfficialDocs.id == docs_id)
        docs_info = (await db.execute(query)).scalars().first()

        if not docs_info:
            return None

        result = {
            'docs_info': docs_info,
            'draft_name': None,
            'draft_dname': None,
            'send_names': [],
            'copy_names': [],
            'share_names': [],
            'file_array': [],
        }

        if docs_info.draft_uid:
            draft_user = (
                await db.execute(select(SysUser).where(SysUser.user_id == docs_info.draft_uid))
            ).scalars().first()
            if draft_user:
                result['draft_name'] = draft_user.nick_name or draft_user.user_name

        if docs_info.did:
            draft_dept = (
                await db.execute(select(SysDept).where(SysDept.dept_id == docs_info.did))
            ).scalars().first()
            if draft_dept:
                result['draft_dname'] = draft_dept.dept_name

        if docs_info.send_uids:
            send_uid_list = []
            for uid in docs_info.send_uids.split(','):
                uid = uid.strip()
                if uid and uid.isdigit():
                    send_uid_list.append(int(uid))
            if send_uid_list:
                send_users = (
                    await db.execute(select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id.in_(send_uid_list)))
                ).all()
                result['send_names'] = [u.nick_name or u.user_name for u in send_users]

        if docs_info.copy_uids:
            copy_uid_list = []
            for uid in docs_info.copy_uids.split(','):
                uid = uid.strip()
                if uid and uid.isdigit():
                    copy_uid_list.append(int(uid))
            if copy_uid_list:
                copy_users = (
                    await db.execute(select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id.in_(copy_uid_list)))
                ).all()
                result['copy_names'] = [u.nick_name or u.user_name for u in copy_users]

        if docs_info.share_uids:
            share_uid_list = []
            for uid in docs_info.share_uids.split(','):
                uid = uid.strip()
                if uid and uid.isdigit():
                    share_uid_list.append(int(uid))
            if share_uid_list:
                share_users = (
                    await db.execute(select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id.in_(share_uid_list)))
                ).all()
                result['share_names'] = [u.nick_name or u.user_name for u in share_users]

        return result

    @classmethod
    async def get_official_docs_list(
            cls, db: AsyncSession, query_object: OfficialDocsPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取公文列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 公文列表信息对象
        """
        from fastapi import Request
        from module_admin.entity.vo.user_vo import CurrentUserModel
        
        query = select(OaOfficialDocs).where(OaOfficialDocs.delete_time == 0)

        # 处理 tab 参数筛选
        if hasattr(query_object, 'tab') and query_object.tab is not None:
            user_id = getattr(query_object, '_user_id', 0)
            
            if query_object.tab == 1:
                # 我创建的
                if user_id:
                    query = query.where(OaOfficialDocs.admin_id == user_id)
            elif query_object.tab == 2:
                # 待我审批
                if user_id:
                    query = query.where(
                        OaOfficialDocs.check_status == 1,
                        func.find_in_set(str(user_id), OaOfficialDocs.check_uids)
                    )
            elif query_object.tab == 3:
                # 我已审批
                if user_id:
                    query = query.where(
                        func.find_in_set(str(user_id), OaOfficialDocs.check_history_uids)
                    )
            elif query_object.tab == 4:
                # 我抄送的
                if user_id:
                    query = query.where(
                        func.find_in_set(str(user_id), OaOfficialDocs.copy_uids)
                    )

        if query_object.keywords:
            query = query.where(
                OaOfficialDocs.title.like(f'%{query_object.keywords}%')
            )

        if query_object.secrets_filter is not None:
            query = query.where(OaOfficialDocs.secrets == query_object.secrets_filter)

        if query_object.urgency_filter is not None:
            query = query.where(OaOfficialDocs.urgency == query_object.urgency_filter)

        query = query.order_by(OaOfficialDocs.create_time.desc()).distinct()

        docs_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return docs_list

    @classmethod
    async def get_pending_docs_list(
            cls, db: AsyncSession, query_object: PendingOfficialDocsModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取待审公文列表

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 待审公文列表信息对象
        """
        query = select(OaOfficialDocs).where(
            OaOfficialDocs.delete_time == 0,
            OaOfficialDocs.check_status == 1,
            func.find_in_set(str(user_id), OaOfficialDocs.check_uids),
            )

        if query_object.keywords:
            query = query.where(OaOfficialDocs.title.like(f'%{query_object.keywords}%'))

        query = query.order_by(OaOfficialDocs.create_time.desc()).distinct()

        docs_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return docs_list

    @classmethod
    async def get_reviewed_docs_list(
            cls, db: AsyncSession, query_object: ReviewedOfficialDocsModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取已审公文列表

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 已审公文列表信息对象
        """
        query = select(OaOfficialDocs).where(
            OaOfficialDocs.delete_time == 0,
            OaOfficialDocs.check_status == 2,
            func.find_in_set(str(user_id), OaOfficialDocs.check_history_uids),
            )

        if query_object.keywords:
            query = query.where(OaOfficialDocs.title.like(f'%{query_object.keywords}%'))

        query = query.order_by(OaOfficialDocs.create_time.desc()).distinct()

        docs_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return docs_list

    @classmethod
    async def add_official_docs_dao(cls, db: AsyncSession, docs: OfficialDocsModel) -> OaOfficialDocs:
        """
        新增公文数据库操作

        :param db: orm 对象
        :param docs: 公文对象
        :return:
        """
        # 只取数据库中实际存在的字段
        docs_dict = {
            k: v for k, v in docs.model_dump().items()
            if k not in {
                'secrets_str', 'urgency_str', 'check_status_str',
                'draft_name', 'draft_dname', 'send_names', 'copy_names',
                'share_names', 'file_array'
            } and v is not None
        }
        db_docs = OaOfficialDocs(**docs_dict)
        db.add(db_docs)
        await db.flush()

        return db_docs

    @classmethod
    async def edit_official_docs_dao(cls, db: AsyncSession, docs_id: int, docs: dict) -> None:
        """
        编辑公文数据库操作

        :param db: orm 对象
        :param docs_id: 公文 ID
        :param docs: 需要更新的公文字典（不包含 id）
        :return:
        """
        await db.execute(
            update(OaOfficialDocs)
            .where(OaOfficialDocs.id == docs_id)
            .values(**docs)
        )

    @classmethod
    async def delete_official_docs_dao(cls, db: AsyncSession, docs: OfficialDocsModel) -> None:
        """
        删除公文数据库操作（逻辑删除）

        :param db: orm 对象
        :param docs: 公文对象
        :return:
        """
        update_time = docs.update_time if docs.update_time is not None else int(datetime.now().timestamp())
        delete_time = update_time
        await db.execute(
            update(OaOfficialDocs)
            .where(OaOfficialDocs.id.in_([docs.id]))
            .values(delete_time=delete_time, update_time=update_time)
        )

    @classmethod
    async def get_official_count(cls, db: AsyncSession, user_id: int):
        """
        获取待审公文数量

        :param db: orm 对象
        :param user_id: 用户 ID
        :return: 待审公文数量
        """
        query = select(func.count()).select_from(OaOfficialDocs).where(
            OaOfficialDocs.delete_time == 0,
            OaOfficialDocs.check_status == 1,
            func.find_in_set(str(user_id), OaOfficialDocs.check_uids),
        )
        result = await db.execute(query)
        count = result.scalar()
        return count
