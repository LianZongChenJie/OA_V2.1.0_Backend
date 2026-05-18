from os.path import join

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.post_do import SysPost
from module_admin.entity.do.user_do import SysUser, SysUserPost
from utils.page_util import PageUtil
from module_personnel.entity.vo.personnel_quit_vo import OaPersonalQuitBaseModel, OaPersonnelQuitPageQueryModel
from module_personnel.entity.do.personnel_quit_do import OaPersonalQuit
from typing import Any
from datetime import datetime

class PersonnelQuitDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaPersonnelQuitPageQueryModel,
                            data_scope_sql: ColumnElement, user_id:int,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        post_subq = (
            select(
                SysUserPost.user_id,
                func.group_concat(SysPost.post_name, ',').label('post_names')
            )
            .join(SysPost, SysUserPost.post_id == SysPost.post_id)
            .group_by(SysUserPost.user_id)
            .subquery("post_agg")
        )

        connect_ji_subq = (
            select(
                OaPersonalQuit.id.label("quit_id"),
                func.group_concat(SysUser.nick_name, ',').label("rec_ji_names")
            )
            .join(SysUser, func.find_in_set(SysUser.user_id, OaPersonalQuit.connect_uids))
            .group_by(OaPersonalQuit.id)
            .subquery("conn_agg")
        )

        leader_subq = (
            select(
                SysDept.dept_id,
                func.group_concat(SysUser.nick_name, ',').label('leader_names')
            )
            .join(SysUser, func.find_in_set(SysUser.user_id, SysDept.leader_id) > 0)
            .group_by(SysDept.dept_id)
            .subquery("leader_agg")
        )
        check_subq = (
            select(
                OaPersonalQuit.id.label("quit_id"),
                func.group_concat(SysUser.nick_name, ',').label("check_names")
            )
            .join(SysUser, func.find_in_set(SysUser.user_id, OaPersonalQuit.check_uids))
            .group_by(OaPersonalQuit.id)
            .subquery("check_agg")
        )

        # 构建基础查询
        quit_user = aliased(SysUser, name="quit")
        rec_user = aliased(SysUser, name="rec")
        admin_user = aliased(SysUser, name="admin")
        lead_user = aliased(SysUser, name="lead")  # 这里注意：lead 是直接关联 lead_admin_id，不再通过部门
        dept_tbl = aliased(SysDept, name="dept")

        # 主查询：每个离职申请只对应一行，然后左连接各个聚合子查询
        query = (
            select(
                OaPersonalQuit,
                quit_user.nick_name.label('user_name'),
                rec_user.nick_name.label('rec_name'),
                admin_user.nick_name.label('admin_name'),
                dept_tbl.dept_name.label('dept_name'),
                post_subq.c.post_names.label('post_name'),  # 已聚合好的岗位
                leader_subq.c.leader_names.label('lead_name'),  # 已聚合好的部门负责人
                connect_ji_subq.c.rec_ji_names.label('rec_ji_names'),  # 已聚合好的交接人
                check_subq.c.check_names.label('check_names'),  # 已聚合好的检查人
            )
            .outerjoin(quit_user, quit_user.user_id == OaPersonalQuit.uid)
            .outerjoin(rec_user, rec_user.user_id == OaPersonalQuit.connect_id)
            .outerjoin(admin_user, admin_user.user_id == OaPersonalQuit.admin_id)
            .outerjoin(lead_user, lead_user.user_id == OaPersonalQuit.lead_admin_id)  # 如果 lead_admin_id 是单个用户ID
            .outerjoin(dept_tbl, quit_user.dept_id == dept_tbl.dept_id)
            .outerjoin(post_subq, quit_user.user_id == post_subq.c.user_id)
            .outerjoin(leader_subq, dept_tbl.dept_id == leader_subq.c.dept_id)
            .outerjoin(connect_ji_subq, OaPersonalQuit.id == connect_ji_subq.c.quit_id)
            .outerjoin(check_subq, OaPersonalQuit.id == check_subq.c.quit_id)
        )

        # 构建条件列表
        conditions = []

        # 通用条件：审核状态
        conditions.append(OaPersonalQuit.delete_time == 0)
        if query_object.check_status:
            conditions.append(OaPersonalQuit.check_status == query_object.check_status)

        if query_object.dept_ids:
            conditions.append(func.find_in_set(quit_user.dept_id, query_object.dept_ids) > 0)

        if query_object.check_status is not None:
            conditions.append(OaPersonalQuit.check_status == query_object.check_status)

        # 通用条件：审核时间范围
        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d").timestamp() + 86399)
            conditions.append(OaPersonalQuit.create_time.between(start_timestamp, end_timestamp))

        # 根据不同的查询条件添加特定条件
        if query_object.admin_id:
            conditions.append(OaPersonalQuit.admin_id == query_object.admin_id)

        if query_object.tab == 1:
            conditions.append(OaPersonalQuit.admin_id == user_id)
        if query_object.tab == 2:
            conditions.append(func.find_in_set(user_id, OaPersonalQuit.check_uids) > 0)
        if query_object.tab == 3:
            conditions.append(func.find_in_set(user_id, OaPersonalQuit.check_history_uids) > 0)
        if query_object.tab == 4:
            conditions.append(func.find_in_set(user_id, OaPersonalQuit.check_copy_uids) > 0)

        elif query_object.check_uids:
            conditions.append(func.find_in_set(query_object.check_uids, OaPersonalQuit.check_uids) > 0)

        elif query_object.check_history_uids:
            conditions.append(
                func.find_in_set(query_object.check_history_uids, OaPersonalQuit.check_history_uids) > 0)

        elif query_object.check_copy_uids:
            conditions.append(func.find_in_set(query_object.check_copy_uids, OaPersonalQuit.check_copy_uids) > 0)

        else:
            # 没有特定条件时，使用 OR 组合
            or_conditions = []
            if query_object.admin_id:
                or_conditions.append(OaPersonalQuit.admin_id == query_object.admin_id)
            if query_object.check_uids:
                or_conditions.append(func.find_in_set(query_object.check_uids, OaPersonalQuit.check_uids) > 0)
            if query_object.check_copy_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_copy_uids, OaPersonalQuit.check_copy_uids) > 0)
            if query_object.check_history_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_history_uids, OaPersonalQuit.check_history_uids) > 0)

            if or_conditions:
                conditions.append(or_(*or_conditions))

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions).group_by(OaPersonalQuit.uid)

        # 排序
        query = query.order_by(desc(OaPersonalQuit.create_time))

        # 分页查询
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaPersonalQuitBaseModel):
        db_model = OaPersonalQuit(**model.model_dump(exclude={"id", "create_time","quit_time"}, exclude_none=True),
                                 create_time=model.create_time, quit_time = model.quit_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaPersonalQuitBaseModel):
        result = await db.execute(
            update(OaPersonalQuit)
            .values(
                **model.model_dump(exclude={"id", "update_time"}, exclude_none=True),update_time=model.update_time
            )
            .where(OaPersonalQuit.id == model.id)
        )
        await db.commit()
        return await cls.get_info_by_id(db, model.id)

    @classmethod
    async def get_info_dict(cls, db: AsyncSession, id: int):
        post_subq = (
            select(
                SysUserPost.user_id,
                func.group_concat(SysPost.post_name, ',').label('post_names')
            )
            .join(SysPost, SysUserPost.post_id == SysPost.post_id)
            .group_by(SysUserPost.user_id)
            .subquery("post_agg")
        )

        connect_ji_subq = (
            select(
                OaPersonalQuit.id.label("quit_id"),
                func.group_concat(SysUser.nick_name, ',').label("rec_ji_names")
            )
            .join(SysUser, func.find_in_set(SysUser.user_id, OaPersonalQuit.connect_uids))
            .group_by(OaPersonalQuit.id)
            .subquery("conn_agg")
        )

        leader_subq = (
            select(
                SysDept.dept_id,
                func.group_concat(SysUser.nick_name, ',').label('leader_names')
            )
            .join(SysUser, func.find_in_set(SysUser.user_id, SysDept.leader_id) > 0)
            .group_by(SysDept.dept_id)
            .subquery("leader_agg")
        )
        # 构建基础查询
        quit_user = aliased(SysUser, name="quit")
        rec_user = aliased(SysUser, name="rec")
        admin_user = aliased(SysUser, name="admin")
        lead_user = aliased(SysUser, name="lead")  # 这里注意：lead 是直接关联 lead_admin_id，不再通过部门
        dept_tbl = aliased(SysDept, name="dept")

        # 主查询：每个离职申请只对应一行，然后左连接各个聚合子查询
        query = (
            select(
                OaPersonalQuit,
                quit_user.nick_name.label('user_name'),
                rec_user.nick_name.label('rec_name'),
                admin_user.nick_name.label('admin_name'),
                dept_tbl.dept_name.label('dept_name'),
                post_subq.c.post_names.label('post_name'),  # 已聚合好的岗位
                leader_subq.c.leader_names.label('lead_name'),  # 已聚合好的部门负责人
                connect_ji_subq.c.rec_ji_names.label('rec_ji_names'),  # 已聚合好的交接人
            )
            .outerjoin(quit_user, quit_user.user_id == OaPersonalQuit.uid)
            .outerjoin(rec_user, rec_user.user_id == OaPersonalQuit.connect_id)
            .outerjoin(admin_user, admin_user.user_id == OaPersonalQuit.admin_id)
            .outerjoin(lead_user, lead_user.user_id == OaPersonalQuit.lead_admin_id)  # 如果 lead_admin_id 是单个用户ID
            .outerjoin(dept_tbl, quit_user.dept_id == dept_tbl.dept_id)
            .outerjoin(post_subq, quit_user.user_id == post_subq.c.user_id)
            .outerjoin(leader_subq, dept_tbl.dept_id == leader_subq.c.dept_id)
            .outerjoin(connect_ji_subq, OaPersonalQuit.id == connect_ji_subq.c.quit_id)
        ).where(OaPersonalQuit.id == id)
        result = await db.execute(query)
        return result.mappings().first()
    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaPersonalQuit)
        .where(
            OaPersonalQuit.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_uid(cls, db: AsyncSession, model: OaPersonalQuitBaseModel) -> OaPersonalQuit | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_info = (
            (
                await db.execute(
                    select(OaPersonalQuit)
                    .where(
                        OaPersonalQuit.uid == model.uid if model.uid else True
                        and OaPersonalQuit.check_status != 2 if model.check_status else True
                    )
                    .order_by(desc(OaPersonalQuit.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaPersonalQuit).values(delete_time=int(datetime.now().timestamp())).where(OaPersonalQuit.id == id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def count_by_uid(cls, db: AsyncSession, uid: str):
        result = await db.execute(select(func.count()).where(OaPersonalQuit.uid == uid))
        return result.scalar()