from operator import and_

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.sql import ColumnElement, func,or_
from sqlalchemy.orm import aliased
from common.vo import PageModel
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.seal_cate_do import SysSealCate
from module_admin.entity.do.user_do import SysUser
from module_basicdata.entity.do.public.flow_do import OaFlow
from module_personnel.dao.flow_record_dao import FlowRecordDao
from utils.page_util import PageUtil
from module_administrative.entity.vo.seal_vo import OaSealBaseModel, OaSealPageQueryModel
from module_administrative.entity.do.seal_do import OaSeal
from typing import Any
from datetime import datetime

from utils.review_util import ReviewUtil


class SealDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaSealPageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 构建基础查询
        # 创建别名
        user = aliased(SysUser, name='user')
        admin = aliased(SysUser, name='admin')
        did_name = aliased(SysDept, name='did_name')
        last_checker = aliased(SysUser, name='last_checker')
        query = select(
            OaSeal,
            did_name.dept_name.label('did_dept'),
            admin.nick_name.label('admin_name'),
            last_checker.nick_name.label('check_last_name')
        ).join(
            user, OaSeal.admin_id == user.user_id, isouter=True
        ).join(
            did_name, OaSeal.did == did_name.dept_id, isouter=True
        ).join(
            admin, OaSeal.admin_id == admin.user_id, isouter=True
        ).join(
            last_checker, OaSeal.check_last_uid == last_checker.user_id, isouter=True
        )

        # 构建条件列表
        conditions = []
        conditions.append(OaSeal.delete_time == 0)
        # 通用条件：审核状态
        if query_object.check_status is not None:
            conditions.append(OaSeal.check_status == query_object.check_status)

        # 通用条件：审核时间范围
        # if query_object.begin_time and query_object.end_time:
        #     start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
        #     end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
        #     conditions.append(OaSeal.check_time.between(start_timestamp, end_timestamp))

        # 根据不同的查询条件添加特定条件
        if query_object.admin_id:
            conditions.append(OaSeal.admin_id == query_object.admin_id)

        if query_object.seal_cate_id:
            conditions.append(OaSeal.seal_cate_id == query_object.seal_cate_id)

        if query_object.keyword:
            conditions.append(OaSeal.title.like(f"%{query_object.keyword}%"))

        elif query_object.check_uids:
            conditions.append(func.find_in_set(query_object.check_uids, OaSeal.check_uids) > 0)

        elif query_object.check_history_uids:
            conditions.append(
                func.find_in_set(query_object.check_history_uids, OaSeal.check_history_uids) > 0)

        elif query_object.check_copy_uids:
            conditions.append(func.find_in_set(query_object.check_copy_uids, OaSeal.check_copy_uids) > 0)

        else:
            # 没有特定条件时，使用 OR 组合
            or_conditions = []
            if query_object.admin_id:
                or_conditions.append(OaSeal.admin_id == query_object.admin_id)
            if query_object.check_uids:
                or_conditions.append(func.find_in_set(query_object.check_uids, OaSeal.check_uids) > 0)
            if query_object.check_copy_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_copy_uids, OaSeal.check_copy_uids) > 0)
            if query_object.check_history_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_history_uids, OaSeal.check_history_uids) > 0)


            if or_conditions:
                conditions.append(or_(*or_conditions))

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaSeal.create_time))

        # 分页查询
        page_list = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        await ReviewUtil.enrich_checker_names_for_rows('OaSeal',db, page_list)
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaSealBaseModel):
        db_model = OaSeal(**model.model_dump(exclude={"id", "create_time", "use_time", "start_time", "end_time","check_time"}, exclude_none=True),
                                 create_time=model.create_time)
        db_model.use_time = model.use_time
        db_model.start_time = model.start_time
        db_model.end_time = model.end_time
        db_model.check_time = model.check_time
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaSealBaseModel):
        result = await db.execute(
            update(OaSeal)
            .values(
                **model.model_dump(exclude={"id", "update_time", 'use_time', 'start_time', 'end_time'}, exclude_none=True)
                , update_time=model.update_time
                , use_time=model.use_time
                ,start_time=model.start_time
                ,end_time=model.end_time
            )
            .where(OaSeal.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        # query = (select(OaSeal)
        # .where(
        #     OaSeal.id == id))
        # link_info = await db.scalar(query)
        # 创建别名
        user = aliased(SysUser, name='user')
        admin = aliased(SysUser, name='admin')
        did_name = aliased(SysDept, name='did_name')
        last_checker = aliased(SysUser, name='last_checker')
        query = select(
            OaSeal,
            did_name.dept_name.label('did_dept'),
            admin.nick_name.label('admin_name'),
            last_checker.nick_name.label('check_last_name'),
            SysSealCate.title.label('cate_name')
        ).join(
            user, OaSeal.admin_id == user.user_id, isouter=True
        ).join(
            did_name, OaSeal.did == did_name.dept_id, isouter=True
        ).join(
            admin, OaSeal.admin_id == admin.user_id, isouter=True
        ).join(
            last_checker, OaSeal.check_last_uid == last_checker.user_id, isouter=True
        ).join(
            SysSealCate, SysSealCate.id == OaSeal.seal_cate_id, isouter=True
        ).where(OaSeal.id == id)
        result = await db.execute(query)
        row = result.first()
        if not row:
            return None
        seal = row[0]
        info = {
            # ========== 基本信息 ==========
            'id': seal.id,
            'title': seal.title,
            'seal_cate_id': seal.seal_cate_id,
            'seal_cate_name': getattr(row, 'cate_name', None),
            'content': seal.content,
            'num': seal.num,
            'status': seal.status,

            # ========== 用印信息 ==========
            'did': seal.did,
            'use_time': seal.use_time,
            'is_borrow': seal.is_borrow,
            'start_time': seal.start_time,
            'end_time': seal.end_time,

            # ========== 附件信息 ==========
            'file_ids': seal.file_ids,

            # ========== 创建人信息 ==========
            'admin_id': seal.admin_id,

            # ========== 审核信息 ==========
            'check_status': seal.check_status,
            'check_flow_id': seal.check_flow_id,
            'check_step_sort': seal.check_step_sort,
            'check_uids': seal.check_uids,
            'check_last_uid': seal.check_last_uid,
            'check_history_uids': seal.check_history_uids,
            'check_copy_uids': seal.check_copy_uids,
            'check_time': seal.check_time,

            # ========== 时间戳 ==========
            'create_time': seal.create_time,
            'update_time': seal.update_time,
            'delete_time': seal.delete_time,

            # ========== 关联字段（从 JOIN 查询获取）==========
            'did_name': getattr(row, 'did_dept', None),
            'admin_name': getattr(row, 'admin_name', None),
            'check_last_name': getattr(row, 'check_last_name', None),
            'check_user_names': [],
            'check_user_names_str': '',
            'check_history_names': [],
            'check_history_names_str': '',
        }

        # 补充审批人名称
        info = await ReviewUtil.enrich_checker_names(db, info)

        # 查询审批记录
        records = await FlowRecordDao.get_records_by_action_id(
            db, seal.id, seal.check_flow_id
        )
        info['records'] = records
        return info

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaSeal).values(delete_time=int(datetime.now().timestamp())).where(OaSeal.id == id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def cancel_change(cls, db: AsyncSession, query_model: OaSealBaseModel):
        result = await db.execute(update(OaSeal).values(
            update_time=int(datetime.now().timestamp()),
            check_status=query_model.check_status,
            content=query_model.content,
        ).where(OaSeal.id == query_model.id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def count_by_uid(cls, db: AsyncSession, uid: str):
        result = await db.execute(select(func.count()).where(OaSeal.uid == uid))
        return result.scalar()
    @classmethod
    async def pass_change(cls, db: AsyncSession, data: OaSealBaseModel):
        try:
            result = await db.execute(
                update(OaSeal)
                .values(
                    check_status=2,
                    check_time=data.check_time,
                    content=data.content,
                )
                .where(OaSeal.id == data.id)
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e
        return result.rowcount

    @classmethod
    async def reject_change(cls, db: AsyncSession, data: OaSealBaseModel):
        try:
            result = await db.execute(
                update(OaSeal)
                .values(
                    check_status=3,
                    check_time=data.check_time,
                    content=data.content,
                )
                .where(OaSeal.id == data.id)
            )
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def get_wait_check_count(cls, db: AsyncSession, user_id: int):
        """
        获取待审用章数量

        :param db: orm 对象
        :param user_id: 用户 ID
        :return: 待审用章数量
        """
        query = select(func.count()).select_from(OaSeal).where(
            OaSeal.delete_time == 0,
            OaSeal.check_status == 1,
            func.find_in_set(str(user_id), OaSeal.check_uids),
        )
        result = await db.execute(query)
        count = result.scalar()
        return count
