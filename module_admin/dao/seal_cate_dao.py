from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.seal_cate_do import SysSealCate
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.vo.seal_cate_vo import SealCateModel, SealCatePageQueryModel
from utils.page_util import PageUtil


class SealCateDao:
    """
    印章类别管理模块数据库操作层
    """

    @classmethod
    async def get_seal_cate_detail_by_id(cls, db: AsyncSession, seal_cate_id: int) -> dict[str, Any] | None:
        """
        根据印章类别 id 获取印章类别详细信息

        :param db: orm 对象
        :param seal_cate_id: 印章类别 id
        :return: 印章类别信息对象
        """
        seal_cate_info = (
            (await db.execute(select(SysSealCate).where(SysSealCate.id == seal_cate_id)))
            .scalars()
            .first()
        )

        if not seal_cate_info:
            return None

        result = {
            'seal_cate_info': seal_cate_info,
            'dept_names': [],
            'keeper_name': None,
        }

        # 查询应用部门名称
        if seal_cate_info.dids:
            dept_ids = [int(d.strip()) for d in seal_cate_info.dids.split(',') if d.strip() and d.strip().isdigit()]
            if dept_ids:
                depts = (
                    await db.execute(
                        select(SysDept.dept_name).where(SysDept.dept_id.in_(dept_ids)).order_by(SysDept.dept_id)
                    )
                ).scalars().all()
                result['dept_names'] = list(depts)

        # 查询保管人姓名
        if seal_cate_info.keep_uid and seal_cate_info.keep_uid > 0:
            user = (
                await db.execute(
                    select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id == seal_cate_info.keep_uid)
                )
            ).first()
            if user:
                result['keeper_name'] = user.nick_name or user.user_name

        return result

    @classmethod
    async def get_seal_cate_detail_by_info(cls, db: AsyncSession, seal_cate: SealCateModel) -> SysSealCate | None:
        """
        根据印章类别参数获取印章类别信息

        :param db: orm 对象
        :param seal_cate: 印章类别参数对象
        :return: 印章类别信息对象
        """
        query_conditions = []
        if seal_cate.id is not None:
            query_conditions.append(SysSealCate.id == seal_cate.id)
        if seal_cate.title:
            query_conditions.append(SysSealCate.title == seal_cate.title)

        if query_conditions:
            seal_cate_info = (
                (await db.execute(select(SysSealCate).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            seal_cate_info = None

        return seal_cate_info

    @classmethod
    async def get_seal_cate_list(
            cls, db: AsyncSession, query_object: SealCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取印章类别列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 印章类别列表信息对象
        """
        query = (
            select(SysSealCate)
            .where(
                SysSealCate.status != -1,
                SysSealCate.title.like(f'%{query_object.title}%') if query_object.title else True,
                SysSealCate.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(SysSealCate.create_time.asc())
            .distinct()
        )
        seal_cate_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        # 处理列表数据，添加扩展字段
        if isinstance(seal_cate_list, PageModel):
            processed_rows = []
            for row in seal_cate_list.rows:
                item = await cls._process_seal_cate_row(db, row)
                processed_rows.append(item)
            seal_cate_list.rows = processed_rows
        elif isinstance(seal_cate_list, list):
            processed_list = []
            for row in seal_cate_list:
                item = await cls._process_seal_cate_row(db, row)
                processed_list.append(item)
            seal_cate_list = processed_list

        return seal_cate_list

    @classmethod
    async def _process_seal_cate_row(cls, db: AsyncSession, row: Any) -> dict[str, Any]:
        """
        处理印章类别行数据，添加扩展字段

        :param db: orm 对象
        :param row: 印章类别行数据（可能是字典或对象）
        :return: 处理后的字典数据
        """
        # 判断是字典还是对象
        if isinstance(row, dict):
            row_id = row.get('id')
            row_dids = row.get('dids')
            row_keep_uid = row.get('keepUid') or row.get('keep_uid')
            result = {
                'id': row_id,
                'title': row.get('title'),
                'dids': row_dids,
                'keepUid': row_keep_uid,
                'keep_uid': row_keep_uid,
                'status': row.get('status'),
                'remark': row.get('remark'),
                'createTime': row.get('createTime') or row.get('create_time'),
                'updateTime': row.get('updateTime') or row.get('update_time'),
                'create_time': row.get('createTime') or row.get('create_time'),
                'update_time': row.get('updateTime') or row.get('update_time'),
                'deptNames': [],
                'dept_names': [],
                'keeperName': None,
                'keeper_name': None,
            }
        else:
            # ORM 对象
            row_id = row.id
            row_dids = row.dids
            row_keep_uid = row.keep_uid
            result = {
                'id': row_id,
                'title': row.title,
                'dids': row_dids,
                'keepUid': row_keep_uid,
                'keep_uid': row_keep_uid,
                'status': row.status,
                'remark': row.remark,
                'createTime': row.create_time,
                'updateTime': row.update_time,
                'create_time': row.create_time,
                'update_time': row.update_time,
                'deptNames': [],
                'dept_names': [],
                'keeperName': None,
                'keeper_name': None,
            }

        # 查询应用部门名称
        if row_dids:
            dept_ids = [int(d.strip()) for d in str(row_dids).split(',') if d.strip() and d.strip().isdigit()]
            if dept_ids:
                depts = (
                    await db.execute(
                        select(SysDept.dept_name).where(SysDept.dept_id.in_(dept_ids)).order_by(SysDept.dept_id)
                    )
                ).scalars().all()
                dept_names_list = list(depts)
                result['dept_names'] = dept_names_list
                result['deptNames'] = dept_names_list

        # 查询保管人姓名
        if row_keep_uid and int(row_keep_uid) > 0:
            user = (
                await db.execute(
                    select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id == int(row_keep_uid))
                )
            ).first()
            if user:
                keeper_name = user.nick_name or user.user_name
                result['keeper_name'] = keeper_name
                result['keeperName'] = keeper_name

        return result

    @classmethod
    async def add_seal_cate_dao(cls, db: AsyncSession, seal_cate_data: dict) -> SysSealCate:
        """
        新增印章类别数据库操作

        :param db: orm 对象
        :param seal_cate_data: 印章类别数据字典
        :return:
        """
        db_seal_cate = SysSealCate(**seal_cate_data)
        db.add(db_seal_cate)
        await db.flush()

        return db_seal_cate

    @classmethod
    async def edit_seal_cate_dao(cls, db: AsyncSession, seal_cate: dict) -> None:
        """
        编辑印章类别数据库操作

        :param db: orm 对象
        :param seal_cate: 需要更新的印章类别字典
        :return:
        """
        seal_cate_id = seal_cate.pop('id', None)
        if seal_cate_id:
            await db.execute(
                update(SysSealCate)
                .where(SysSealCate.id == seal_cate_id)
                .values(**seal_cate)
            )

    @classmethod
    async def delete_seal_cate_dao(cls, db: AsyncSession, seal_cate: SealCateModel) -> None:
        """
        删除印章类别数据库操作（逻辑删除）

        :param db: orm 对象
        :param seal_cate: 印章类别对象
        :return:
        """
        update_time = seal_cate.update_time if seal_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysSealCate)
            .where(SysSealCate.id.in_([seal_cate.id]))
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_seal_cate_dao(cls, db: AsyncSession, seal_cate: SealCateModel) -> None:
        """
        禁用印章类别数据库操作

        :param db: orm 对象
        :param seal_cate: 印章类别对象
        :return:
        """
        update_time = seal_cate.update_time if seal_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysSealCate)
            .where(SysSealCate.id == seal_cate.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_seal_cate_dao(cls, db: AsyncSession, seal_cate: SealCateModel) -> None:
        """
        启用印章类别数据库操作

        :param db: orm 对象
        :param seal_cate: 印章类别对象
        :return:
        """
        update_time = seal_cate.update_time if seal_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysSealCate)
            .where(SysSealCate.id == seal_cate.id)
            .values(status=1, update_time=update_time)
        )

