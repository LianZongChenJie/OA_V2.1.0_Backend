from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.customer_do import OaCustomer
from module_admin.entity.vo.customer_vo import CustomerModel, CustomerPageQueryModel
from utils.page_util import PageUtil


class CustomerDao:
    """
    客户管理模块数据库操作层
    """

    @classmethod
    async def get_customer_detail_by_id(cls, db: AsyncSession, customer_id: int) -> dict[str, Any] | None:
        """
        根据客户 id 获取客户详细信息

        :param db: orm 对象
        :param customer_id: 客户 id
        :return: 客户详细信息对象
        """
        query = select(OaCustomer).where(OaCustomer.id == customer_id)
        customer_info = (await db.execute(query)).scalars().first()

        if not customer_info:
            return None

        result = {
            'customer_info': customer_info,
            'belong_name': None,
            'belong_department': None,
            'industry': None,
            'grade': None,
            'source': None,
            'customer_status_name': None,
            'intent_status_name': None,
            'contact_name': None,
            'contact_mobile': None,
            'contact_email': None,
            'share_names': [],
        }

        return result

    @classmethod
    async def get_customer_detail_by_info(cls, db: AsyncSession, customer_info: CustomerModel) -> OaCustomer | None:
        """
        根据客户名称获取客户信息

        :param db: orm 对象
        :param customer_info: 客户对象
        :return: 客户信息
        """
        conditions = [
            OaCustomer.delete_time == 0,
            OaCustomer.discard_time == 0
        ]
        
        if customer_info.name:
            conditions.append(OaCustomer.name == customer_info.name)
        
        query = select(OaCustomer).where(*conditions)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def get_customer_list(
            cls, db: AsyncSession, query_object: CustomerPageQueryModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取客户列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 客户列表信息对象
        """
        conditions = [
            OaCustomer.delete_time == 0,
            OaCustomer.discard_time == 0
        ]

        if query_object.keywords:
            conditions.append(
                or_(
                    OaCustomer.id.like(f'%{query_object.keywords}%'),
                    OaCustomer.name.like(f'%{query_object.keywords}%')
                )
            )

        if query_object.customer_status_filter is not None:
            conditions.append(OaCustomer.customer_status == query_object.customer_status_filter)

        if query_object.industry_id_filter is not None:
            conditions.append(OaCustomer.industry_id == query_object.industry_id_filter)

        if query_object.source_id_filter is not None:
            conditions.append(OaCustomer.source_id == query_object.source_id_filter)

        if query_object.grade_id_filter is not None:
            conditions.append(OaCustomer.grade_id == query_object.grade_id_filter)

        if query_object.intent_status_filter is not None:
            conditions.append(OaCustomer.intent_status == query_object.intent_status_filter)

        if query_object.follow_time_start is not None:
            conditions.append(OaCustomer.follow_time >= query_object.follow_time_start)

        if query_object.follow_time_end is not None:
            conditions.append(OaCustomer.follow_time <= query_object.follow_time_end)

        if query_object.next_time_start is not None:
            conditions.append(OaCustomer.next_time >= query_object.next_time_start)

        if query_object.next_time_end is not None:
            conditions.append(OaCustomer.next_time <= query_object.next_time_end)

        # 根据 tab 参数设置查询条件
        if query_object.tab == 0:
            # 全部客户（根据权限过滤）
            pass
        elif query_object.tab == 1:
            # 我的客户
            conditions.append(OaCustomer.belong_uid == user_id)
        elif query_object.tab == 2:
            # 下属客户
            conditions.append(OaCustomer.belong_uid != user_id)
        elif query_object.tab == 3:
            # 分享客户
            conditions.append(func.find_in_set(str(user_id), OaCustomer.share_ids))

        query = select(OaCustomer).where(*conditions)
        query = query.order_by(OaCustomer.create_time.desc())

        customer_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return customer_list

    @classmethod
    async def add_customer_dao(cls, db: AsyncSession, customer: CustomerModel) -> OaCustomer:
        """
        新增客户数据库操作

        :param db: orm 对象
        :param customer: 客户对象
        :return:
        """
        docs_dict = {
            k: v for k, v in customer.model_dump().items()
            if v is not None
        }
        db_customer = OaCustomer(**docs_dict)
        db.add(db_customer)
        await db.flush()

        return db_customer

    @classmethod
    async def edit_customer_dao(cls, db: AsyncSession, customer_id: int, customer: dict) -> None:
        """
        编辑客户数据库操作

        :param db: orm 对象
        :param customer_id: 客户 ID
        :param customer: 需要更新的客户字典
        :return:
        """
        await db.execute(
            update(OaCustomer)
            .where(OaCustomer.id == customer_id)
            .values(**customer)
        )

    @classmethod
    async def discard_customer_dao(cls, db: AsyncSession, customer: CustomerModel) -> None:
        """
        废弃客户数据库操作（逻辑删除）

        :param db: orm 对象
        :param customer: 客户对象
        :return:
        """
        update_time = customer.update_time if customer.update_time is not None else int(datetime.now().timestamp())
        discard_time = update_time
        await db.execute(
            update(OaCustomer)
            .where(OaCustomer.id.in_([customer.id]))
            .values(discard_time=discard_time, update_time=update_time)
        )
