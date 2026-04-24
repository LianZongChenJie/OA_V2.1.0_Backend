from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_contract.entity.do.purchase_do import OaPurchase
from module_contract.entity.vo.purchase_vo import PurchasePageQueryModel
from utils.page_util import PageUtil
from utils.log_util import logger


class PurchaseDao:
    """
    采购合同管理模块数据库操作层
    """

    @classmethod
    async def get_purchase_list(
            cls, db: AsyncSession, query_object: PurchasePageQueryModel, user_id: int,
            auth_dids: str = '', son_dids: str = '', is_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取采购合同列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为管理员
        :param is_page: 是否开启分页
        :return: 采购合同列表信息对象
        """
        conditions = [OaPurchase.delete_time == 0]

        if hasattr(query_object, 'archive_status') and query_object.archive_status == 1:
            conditions.append(OaPurchase.archive_time > 0)
        elif hasattr(query_object, 'stop_status') and query_object.stop_status == 1:
            conditions.append(OaPurchase.stop_time > 0)
        elif hasattr(query_object, 'void_status') and query_object.void_status == 1:
            conditions.append(OaPurchase.void_time > 0)
        else:
            conditions.append(OaPurchase.archive_time == 0)
            conditions.append(OaPurchase.stop_time == 0)
            conditions.append(OaPurchase.void_time == 0)

        if query_object.keywords:
            conditions.append(
                or_(
                    OaPurchase.id.like(f'%{query_object.keywords}%'),
                    OaPurchase.name.like(f'%{query_object.keywords}%'),
                    OaPurchase.code.like(f'%{query_object.keywords}%')
                )
            )

        if query_object.types_filter is not None:
            conditions.append(OaPurchase.types == query_object.types_filter)

        if query_object.cate_id_filter is not None:
            conditions.append(OaPurchase.cate_id == query_object.cate_id_filter)

        if query_object.check_status_filter is not None:
            conditions.append(OaPurchase.check_status == query_object.check_status_filter)

        if query_object.sign_time_start is not None:
            conditions.append(OaPurchase.sign_time >= query_object.sign_time_start)
        if query_object.sign_time_end is not None:
            conditions.append(OaPurchase.sign_time <= query_object.sign_time_end)

        if query_object.end_time_start is not None:
            conditions.append(OaPurchase.end_time >= query_object.end_time_start)
        if query_object.end_time_end is not None:
            conditions.append(OaPurchase.end_time <= query_object.end_time_end)

        if query_object.tab == 0:
            if query_object.admin_id_filter is not None:
                conditions.append(OaPurchase.sign_uid == query_object.admin_id_filter)
        elif query_object.tab == 1:
            conditions.append(func.find_in_set(str(user_id), OaPurchase.check_uids))
        elif query_object.tab == 2:
            conditions.append(func.find_in_set(str(user_id), OaPurchase.check_history_uids))

        if query_object.tab == 0 and not is_admin:
            permission_conditions = [
                OaPurchase.admin_id == user_id,
                OaPurchase.prepared_uid == user_id,
                OaPurchase.sign_uid == user_id,
                OaPurchase.keeper_uid == user_id,
                func.find_in_set(str(user_id), OaPurchase.share_ids),
                func.find_in_set(str(user_id), OaPurchase.check_uids),
                func.find_in_set(str(user_id), OaPurchase.check_history_uids),
                ]

            if auth_dids or son_dids:
                dept_ids = set()
                if auth_dids:
                    dept_ids.update([int(d.strip()) for d in auth_dids.split(',') if d.strip()])
                if son_dids:
                    dept_ids.update([int(d.strip()) for d in son_dids.split(',') if d.strip()])

                if dept_ids:
                    permission_conditions.append(OaPurchase.did.in_(dept_ids))

            if permission_conditions:
                conditions.append(or_(*permission_conditions))

        query = (
            select(OaPurchase)
            .where(*conditions)
            .order_by(OaPurchase.create_time.desc())
            .distinct()
        )

        purchase_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        if isinstance(purchase_list, PageModel) and hasattr(purchase_list, 'rows'):
            processed_rows = []
            for row in purchase_list.rows:
                item = await cls._process_purchase_row(db, row)
                processed_rows.append(item)
            purchase_list.rows = processed_rows
        elif isinstance(purchase_list, list):
            processed_list = []
            for row in purchase_list:
                item = await cls._process_purchase_row(db, row)
                processed_list.append(item)
            purchase_list = processed_list

        return purchase_list

    @classmethod
    async def _process_purchase_row(cls, db: AsyncSession, row: Any) -> dict[str, Any]:
        """
        处理采购合同行数据，添加扩展字段

        :param db: orm 对象
        :param row: 采购合同行数据
        :return: 处理后的字典数据
        """
        from utils.camel_converter import ModelConverter
        from utils.time_format_util import timestamp_to_datetime
        
        if not isinstance(row, dict):
            if hasattr(row, '__table__'):
                row = ModelConverter.to_dict(row, by_alias=True)
            else:
                return row

        row_id = row.get('id')
        cate_id = row.get('cateId')
        prepared_uid = row.get('preparedUid')
        admin_id = row.get('adminId')
        did = row.get('did')
        sign_uid = row.get('signUid')
        keeper_uid = row.get('keeperUid')
        start_time = row.get('startTime')
        end_time = row.get('endTime')
        sign_time = row.get('signTime')
        create_time = row.get('createTime')
        update_time = row.get('updateTime')
        
        result = row.copy()

        result['cateName'] = None
        result['adminName'] = None
        result['preparedName'] = None
        result['deptName'] = None
        result['signName'] = None
        result['keeperName'] = None
        result['startTimeStr'] = None
        result['endTimeStr'] = None
        result['signTimeStr'] = None
        result['createTimeStr'] = None
        result['updateTimeStr'] = None

        if cate_id and int(cate_id) > 0:
            from module_admin.dao.contract_cate_dao import ContractCateDao
            try:
                cate_info = await ContractCateDao.get_contract_cate_detail_by_id(db, int(cate_id))
                if cate_info:
                    result['cateName'] = cate_info.title
                else:
                    logger.warning(f'采购列表 - 未找到合同分类 ID: {cate_id}')
            except Exception as e:
                logger.error(f'采购列表 - 查询合同分类名称失败: {e}, cate_id: {cate_id}')

        if admin_id and int(admin_id) > 0:
            from module_admin.dao.user_dao import UserDao
            admin_result = await UserDao.get_user_by_id(db, int(admin_id))
            if admin_result and admin_result.get('user_basic_info'):
                admin_info = admin_result['user_basic_info']
                result['adminName'] = admin_info.nick_name or admin_info.user_name

        if prepared_uid and int(prepared_uid) > 0:
            from module_admin.dao.user_dao import UserDao
            prepared_result = await UserDao.get_user_by_id(db, int(prepared_uid))
            if prepared_result and prepared_result.get('user_basic_info'):
                prepared_info = prepared_result['user_basic_info']
                result['preparedName'] = prepared_info.nick_name or prepared_info.user_name

        if did and int(did) > 0:
            from module_admin.dao.dept_dao import DeptDao
            dept_info = await DeptDao.get_dept_detail_by_id(db, int(did))
            if dept_info:
                result['deptName'] = dept_info.dept_name

        if sign_uid and int(sign_uid) > 0:
            from module_admin.dao.user_dao import UserDao
            sign_result = await UserDao.get_user_by_id(db, int(sign_uid))
            if sign_result and sign_result.get('user_basic_info'):
                sign_info = sign_result['user_basic_info']
                result['signName'] = sign_info.nick_name or sign_info.user_name

        if keeper_uid and int(keeper_uid) > 0:
            from module_admin.dao.user_dao import UserDao
            keeper_result = await UserDao.get_user_by_id(db, int(keeper_uid))
            if keeper_result and keeper_result.get('user_basic_info'):
                keeper_info = keeper_result['user_basic_info']
                result['keeperName'] = keeper_info.nick_name or keeper_info.user_name

        if start_time and int(start_time) > 0:
            result['startTimeStr'] = timestamp_to_datetime(int(start_time), '%Y-%m-%d')

        if end_time and int(end_time) > 0:
            result['endTimeStr'] = timestamp_to_datetime(int(end_time), '%Y-%m-%d')

        if sign_time and int(sign_time) > 0:
            result['signTimeStr'] = timestamp_to_datetime(int(sign_time), '%Y-%m-%d')

        if create_time and int(create_time) > 0:
            result['createTimeStr'] = timestamp_to_datetime(int(create_time), '%Y-%m-%d %H:%M:%S')

        if update_time and int(update_time) > 0:
            result['updateTimeStr'] = timestamp_to_datetime(int(update_time), '%Y-%m-%d %H:%M:%S')

        return result

    @classmethod
    async def add(cls, db: AsyncSession, model: dict[str, Any]):
        """
        新增采购合同

        :param db: orm 对象
        :param model: 采购合同模型字典
        :return:
        """
        db_model = OaPurchase(**model)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, model: dict[str, Any]):
        """
        更新采购合同

        :param db: orm 对象
        :param model: 采购合同模型字典
        :return:
        """
        from sqlalchemy import update
        result = await db.execute(
            update(OaPurchase)
            .values(**model)
            .where(OaPurchase.id == model.get('id'))
        )
        return result.rowcount

    @classmethod
    async def delete(cls, db: AsyncSession, purchase_id: int, update_time: int):
        """
        删除采购合同（逻辑删除）

        :param db: orm 对象
        :param purchase_id: 采购合同 ID
        :param update_time: 更新时间
        :return:
        """
        from sqlalchemy import update
        result = await db.execute(
            update(OaPurchase)
            .values(delete_time=update_time, update_time=update_time)
            .where(OaPurchase.id == purchase_id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_by_id(cls, db: AsyncSession, purchase_id: int) -> OaPurchase | None:
        """
        根据 ID 获取采购合同详情

        :param db: orm 对象
        :param purchase_id: 采购合同 ID
        :return: 采购合同对象
        """
        query = select(OaPurchase).where(
            OaPurchase.id == purchase_id,
            OaPurchase.delete_time == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_name(cls, db: AsyncSession, purchase_data: dict) -> OaPurchase | None:
        """
        根据名称获取采购合同（用于验重）

        :param db: orm 对象
        :param purchase_data: 采购合同数据
        :return: 采购合同对象
        """
        query = select(OaPurchase).where(
            OaPurchase.name == purchase_data.get('name'),
            OaPurchase.delete_time == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def archive_purchase(cls, db: AsyncSession, purchase_id: int, archive_uid: int, archive_time: int) -> int:
        """
        归档采购合同

        :param db: orm 对象
        :param purchase_id: 采购合同 ID
        :param archive_uid: 归档人 ID
        :param archive_time: 归档时间
        :return: 影响行数
        """
        from sqlalchemy import update
        result = await db.execute(
            update(OaPurchase)
            .values(
                archive_uid=archive_uid,
                archive_time=archive_time,
                update_time=archive_time
            )
            .where(OaPurchase.id == purchase_id)
        )
        await db.commit()
        return result.rowcount


