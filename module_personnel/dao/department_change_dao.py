from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.user_do import SysUser
from module_personnel.dao.flow_record_dao import FlowRecordDao
from utils.page_util import PageUtil
from module_personnel.entity.vo.department_change_vo import OaDepartmentChangePageQueryModel, OaDepartmentChangeBassModel
from module_personnel.entity.do.department_change_do import OaDepartmentChange
from typing import Any
from datetime import datetime
from utils.review_util import ReviewUtil

class DepartmentChangeDao:

    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaDepartmentChangePageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        """
        获取部门变动分页查询列表列表
        """
        # 创建别名
        user = aliased(SysUser, name='user')
        admin = aliased(SysUser, name='admin')
        from_dept = aliased(SysDept, name='from_dept')
        to_dept = aliased(SysDept, name='to_dept')
        last_checker = aliased(SysUser, name='last_checker')

        # 构建基础查询
        query = select(
            OaDepartmentChange,
            user.nick_name.label('nick_name'),
            from_dept.dept_name.label('from_name'),
            to_dept.dept_name.label('to_name'),
            admin.nick_name.label('admin_name'),
            last_checker.nick_name.label('check_last_name')
        ).join(
            user, OaDepartmentChange.uid == user.user_id, isouter=True
        ).join(
            from_dept, OaDepartmentChange.from_did == from_dept.dept_id, isouter=True
        ).join(
            to_dept, OaDepartmentChange.to_did == to_dept.dept_id, isouter=True
        ).join(
            admin, OaDepartmentChange.admin_id == admin.user_id, isouter=True
        ).join(
            last_checker, OaDepartmentChange.check_last_uid == last_checker.user_id, isouter=True
        )

        # 构建条件列表
        conditions = []

        if query_object.check_status is not None:
            conditions.append(OaDepartmentChange.check_status == query_object.check_status)

        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaDepartmentChange.check_time.between(start_timestamp, end_timestamp))

        # 根据不同的查询条件添加特定条件
        if query_object.admin_id:
            conditions.append(OaDepartmentChange.admin_id == query_object.admin_id)

        elif query_object.check_uids:
            conditions.append(func.find_in_set(query_object.check_uids, OaDepartmentChange.check_uids) > 0)

        elif query_object.check_history_uids:
            conditions.append(
                func.find_in_set(query_object.check_history_uids, OaDepartmentChange.check_history_uids) > 0)

        elif query_object.check_copy_uids:
            conditions.append(func.find_in_set(query_object.check_copy_uids, OaDepartmentChange.check_copy_uids) > 0)

        else:
            or_conditions = []
            if query_object.admin_id:
                or_conditions.append(OaDepartmentChange.admin_id == query_object.admin_id)
            if query_object.check_uids:
                or_conditions.append(func.find_in_set(query_object.check_uids, OaDepartmentChange.check_uids) > 0)
            if query_object.check_copy_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_copy_uids, OaDepartmentChange.check_copy_uids) > 0)
            if query_object.check_history_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_history_uids, OaDepartmentChange.check_history_uids) > 0)

            if or_conditions:
                conditions.append(or_(*or_conditions))

        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        if conditions:
            query = query.where(*conditions)

        query = query.order_by(desc(OaDepartmentChange.create_time))

        # 分页查询
        page_list = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        # 补充当前审批人和历史审批人信息
        await ReviewUtil.enrich_checker_names_for_rows('OaDepartmentChange',db, page_list)
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaDepartmentChangeBassModel):
        """
        添加部门变动
        :param db:
        :param model:
        :return:
        """
        db_model = OaDepartmentChange(**model.model_dump(exclude={"id", "create_time",'move_time','connect_time'}, exclude_none=True),
                                 create_time=model.create_time, move_time = model.move_time, connect_time = model.connect_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaDepartmentChangeBassModel):
        """
        更新部门变动
        :param db:
        :param model:
        :return:
        """
        result = await db.execute(
            update(OaDepartmentChange)
            .values(
                **model.model_dump(exclude={"id", "update_time",'move_time', 'connect_time'}, exclude_none=True), update_time=model.update_time, move_time = model.move_time, connect_time = model.connect_time
            )
            .where(OaDepartmentChange.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        """
        获取部门变动详情
        :param db:
        :param id:
        :return:
        """
        # 创建别名
        user = aliased(SysUser, name='user')
        admin = aliased(SysUser, name='admin')
        from_dept = aliased(SysDept, name='from_dept')
        to_dept = aliased(SysDept, name='to_dept')
        last_checker = aliased(SysUser, name='last_checker')

        # 查询基本信息
        stmt = select(
            OaDepartmentChange,
            user.nick_name.label('nick_name'),
            from_dept.dept_name.label('from_name'),
            to_dept.dept_name.label('to_name'),
            admin.nick_name.label('admin_name'),
            last_checker.nick_name.label('check_last_name')
        ).join(
            user, OaDepartmentChange.uid == user.user_id, isouter=True
        ).join(
            from_dept, OaDepartmentChange.from_did == from_dept.dept_id, isouter=True
        ).join(
            to_dept, OaDepartmentChange.to_did == to_dept.dept_id, isouter=True
        ).join(
            admin, OaDepartmentChange.admin_id == admin.user_id, isouter=True
        ).join(
            last_checker, OaDepartmentChange.check_last_uid == last_checker.user_id, isouter=True
        ).where(
            OaDepartmentChange.id == id,
            OaDepartmentChange.delete_time == 0
        )

        result = await db.execute(stmt)
        row = result.first()
        if not row:
            return None

            # 获取实体
        dept_change = row[0]

        # 构建 info 字典
        info = {
            'id': dept_change.id,
            'uid': dept_change.uid,
            'from_did': dept_change.from_did,
            'to_did': dept_change.to_did,
            'connect_id': dept_change.connect_id,
            'connect_time': dept_change.connect_time,
            'connect_uids': dept_change.connect_uids,
            'file_ids': dept_change.file_ids,
            'move_time': dept_change.move_time,
            'status': dept_change.status,
            'remark': dept_change.remark,
            'admin_id': dept_change.admin_id,
            'did': dept_change.did,
            'check_status': dept_change.check_status,
            'check_flow_id': dept_change.check_flow_id,
            'check_step_sort': dept_change.check_step_sort,
            'check_uids': dept_change.check_uids,
            'check_last_uid': dept_change.check_last_uid,
            'check_history_uids': dept_change.check_history_uids,
            'check_copy_uids': dept_change.check_copy_uids,
            'check_time': dept_change.check_time,
            'create_time': dept_change.create_time,
            'update_time': dept_change.update_time,
            'delete_time': dept_change.delete_time,
            # 关联字段
            'nick_name': row.nick_name,
            'from_name': row.from_name,
            'to_name': row.to_name,
            'admin_name': row.admin_name,
            'check_last_name': row.check_last_name
        }

        # 补充审批人名称
        info = await ReviewUtil.enrich_checker_names(db, info)

        # 查询审批记录
        records = await FlowRecordDao.get_records_by_action_id(
            db, dept_change.id, dept_change.check_flow_id
        )
        info['records'] = records
        return info
    @classmethod
    async def get_info_by_uid(cls, db: AsyncSession, model: OaDepartmentChangeBassModel) -> OaDepartmentChange | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_info = (
            (
                await db.execute(
                    select(OaDepartmentChange)
                    .where(
                        OaDepartmentChange.uid == model.uid if model.uid else True
                        and OaDepartmentChange.check_status != 2 if model.check_status else True
                    )
                    .order_by(desc(OaDepartmentChange.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        """
        删除部门变动
        :param db:
        :param id:
        :return:
        """
        result = await db.execute(update(OaDepartmentChange).values(delete_time=int(datetime.now().timestamp())).where(OaDepartmentChange.id == id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def review(cls, db: AsyncSession, data: OaDepartmentChangeBassModel):
        """
        审核部门变动
        :param db:
        :param data:
        :return:
        """
        try:
            await db.execute(
                update(OaDepartmentChange)
                .values(
                    check_status=data.check_status,
                    check_time=data.check_time
                )
                .where(OaDepartmentChange.id == data.id)
            )
            await db.commit()
            return await cls.get_info_by_id(db, data.id)
        except Exception as e:
            await db.rollback()
            raise e