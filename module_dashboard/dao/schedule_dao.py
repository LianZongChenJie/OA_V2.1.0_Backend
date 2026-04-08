from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.sql import ColumnElement, func
from common.vo import PageModel
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.user_do import SysUser
from module_basicdata.entity.do.project.work_cate_do import OaWorkCate
from utils.page_util import PageUtil
from module_dashboard.entity.vo.schedule_vo import OaScheduleBaseModel, OaSchedulePageQueryModel
from module_dashboard.entity.do.schedule_do import OaSchedule
from typing import Any
from datetime import datetime
from utils.log_util import logger

class ScheduleDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaSchedulePageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 构建基础查询
        query = select(OaSchedule,SysUser,SysDept, OaWorkCate).join(SysUser, OaSchedule.admin_id == SysUser.user_id, isouter=True).join(SysDept, SysUser.dept_id == SysDept.dept_id,isouter=True ).join(OaWorkCate, OaSchedule.cid == OaWorkCate.id,isouter=True )

        # 构建条件列表
        conditions = []
        conditions.append(OaSchedule.delete_time == 0)

        # 时间范围筛选（支持 begin_time/end_time 或 range_time）
        if query_object.range_time:
            # 解析 range_time 格式："2024-01-01 至 2024-01-31"
            try:
                range_parts = query_object.range_time.split('至')
                if len(range_parts) == 2:
                    start_timestamp = int(datetime.strptime(range_parts[0].strip(), "%Y-%m-%d").timestamp())
                    end_timestamp = int(datetime.strptime(range_parts[1].strip(), "%Y-%m-%d").timestamp()) + 86399  # 当天结束时间
                    conditions.append(OaSchedule.start_time.between(start_timestamp, end_timestamp))
            except Exception as e:
                logger.warning(f'解析时间范围失败：{str(e)}')
        elif query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaSchedule.start_time.between(start_timestamp, end_timestamp))

        # 关键词搜索（标题或备注）
        if query_object.keywords:
            from sqlalchemy import or_
            conditions.append(
                or_(
                    OaSchedule.title.like(f'%{query_object.keywords}%'),
                    OaSchedule.remark.like(f'%{query_object.keywords}%')
                )
            )

        # 用户ID筛选
        if query_object.uid:
            conditions.append(OaSchedule.admin_id == query_object.uid)

        # 任务ID筛选
        if query_object.tid:
            conditions.append(OaSchedule.tid == query_object.tid)

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaSchedule.create_time))

        # 分页查询
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num if query_object.page_num else 1, 
            query_object.page_size if query_object.page_size else 20, 
            is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaScheduleBaseModel):
        db_model = OaSchedule(**model.model_dump(exclude={"id", "create_time","start_time", "end_time"}, exclude_none=True),
                                 create_time=model.create_time, start_time=model.start_time, end_time=model.end_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaScheduleBaseModel):
        # 构建更新数据，排除 None 值
        update_data = model.model_dump(exclude={"id", "update_time", "start_time", "end_time"}, exclude_none=True)
        
        # 确保必填字段有值
        if 'delete_time' not in update_data or update_data['delete_time'] is None:
            update_data['delete_time'] = 0
        if 'create_time' not in update_data or update_data['create_time'] is None:
            # 查询原始的 create_time
            original = await cls.get_info_by_id(db, model.id)
            if original:
                update_data['create_time'] = original.create_time
            else:
                update_data['create_time'] = int(datetime.now().timestamp())
        
        result = await db.execute(
            update(OaSchedule)
            .values(
                **update_data,
                update_time=model.update_time,
                start_time=model.start_time,
                end_time=model.end_time
            )
            .where(OaSchedule.id == model.id)
        )
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaSchedule)
        .where(
            OaSchedule.id == id))
        info = await db.scalar(query)
        return info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaSchedule).values(delete_time=int(datetime.now().timestamp())).where(OaSchedule.id == id))
        await db.commit()
        return result.rowcount
