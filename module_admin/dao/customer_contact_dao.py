from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.customer_contact_do import OaCustomerContact
from module_admin.entity.vo.customer_contact_vo import CustomerContactModel, CustomerContactPageQueryModel
from utils.page_util import PageUtil


class CustomerContactDao:
    """
    客户联系人管理模块数据库操作层
    """

    @classmethod
    async def get_customer_contact_detail_by_id(cls, db: AsyncSession, contact_id: int) -> dict[str, Any] | None:
        """
        根据联系人 id 获取联系人详细信息

        :param db: orm 对象
        :param contact_id: 联系人 id
        :return: 联系人详细信息对象
        """
        query = select(OaCustomerContact).where(OaCustomerContact.id == contact_id)
        contact_info = (await db.execute(query)).scalars().first()

        if not contact_info:
            return None

        result = {
            'contact_info': contact_info,
            'customer_name': None,
        }

        return result

    @classmethod
    async def get_customer_contact_by_info(cls, db: AsyncSession, contact_info: CustomerContactModel) -> OaCustomerContact | None:
        """
        根据联系人名称和客户 ID 获取联系人信息

        :param db: orm 对象
        :param contact_info: 联系人对象
        :return: 联系人信息
        """
        conditions = [
            OaCustomerContact.delete_time == 0,
        ]
        
        if contact_info.cid:
            conditions.append(OaCustomerContact.cid == contact_info.cid)
        
        if contact_info.name:
            conditions.append(OaCustomerContact.name == contact_info.name)
        
        query = select(OaCustomerContact).where(*conditions)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def get_customer_contact_list(
            cls, db: AsyncSession, query_object: CustomerContactPageQueryModel, user_id: int, 
            where_conditions: list = None, where_or_conditions: list = None, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取联系人列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param where_conditions: WHERE 条件列表
        :param where_or_conditions: WHERE OR 条件列表
        :param is_page: 是否开启分页
        :return: 联系人列表信息对象
        """
        conditions = [
            OaCustomerContact.delete_time == 0,
        ]

        if where_conditions:
            conditions.extend(where_conditions)

        if query_object.keywords:
            conditions.append(
                or_(
                    OaCustomerContact.id.like(f'%{query_object.keywords}%'),
                    OaCustomerContact.name.like(f'%{query_object.keywords}%'),
                    OaCustomerContact.mobile.like(f'%{query_object.keywords}%'),
                    OaCustomerContact.email.like(f'%{query_object.keywords}%')
                )
            )

        if query_object.cid:
            conditions.append(OaCustomerContact.cid == query_object.cid)

        query = select(OaCustomerContact).where(*conditions)
        
        if where_or_conditions:
            query = query.where(or_(*where_or_conditions))
        
        query = query.order_by(OaCustomerContact.create_time.desc())

        contact_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        # 为每个联系人添加客户名称
        if isinstance(contact_list, PageModel) and hasattr(contact_list, 'rows'):
            enhanced_rows = []
            for contact in contact_list.rows:
                # 将 ORM 对象转换为字典
                if isinstance(contact, dict):
                    contact_dict = contact.copy()
                elif hasattr(contact, '__dict__'):
                    contact_dict = {key: value for key, value in contact.__dict__.items() if not key.startswith('_')}
                else:
                    contact_dict = dict(contact) if hasattr(contact, '__iter__') else {}
                
                # 查询客户名称
                cid = contact_dict.get('cid')
                if cid and int(cid) > 0:
                    try:
                        from module_admin.entity.do.customer_do import OaCustomer
                        customer_query = select(OaCustomer).where(OaCustomer.id == cid)
                        customer_info = (await db.execute(customer_query)).scalars().first()
                        if customer_info:
                            contact_dict['customer_name'] = customer_info.name
                    except Exception as e:
                        from utils.log_util import logger
                        logger.error(f'查询客户名称失败: {e}')
                
                enhanced_rows.append(contact_dict)
            contact_list.rows = enhanced_rows
        elif isinstance(contact_list, list):
            enhanced_list = []
            for contact in contact_list:
                # 将 ORM 对象转换为字典
                if isinstance(contact, dict):
                    contact_dict = contact.copy()
                elif hasattr(contact, '__dict__'):
                    contact_dict = {key: value for key, value in contact.__dict__.items() if not key.startswith('_')}
                else:
                    contact_dict = dict(contact) if hasattr(contact, '__iter__') else {}
                
                # 查询客户名称
                cid = contact_dict.get('cid')
                if cid and int(cid) > 0:
                    try:
                        from module_admin.entity.do.customer_do import OaCustomer
                        customer_query = select(OaCustomer).where(OaCustomer.id == cid)
                        customer_info = (await db.execute(customer_query)).scalars().first()
                        if customer_info:
                            contact_dict['customer_name'] = customer_info.name
                    except Exception as e:
                        from utils.log_util import logger
                        logger.error(f'查询客户名称失败: {e}')
                
                enhanced_list.append(contact_dict)
            contact_list = enhanced_list

        return contact_list

    @classmethod
    async def add_customer_contact_dao(cls, db: AsyncSession, contact: CustomerContactModel) -> OaCustomerContact:
        """
        新增联系人数据库操作

        :param db: orm 对象
        :param contact: 联系人对象
        :return:
        """
        docs_dict = {
            k: v for k, v in contact.model_dump().items()
            if v is not None
        }
        db_contact = OaCustomerContact(**docs_dict)
        db.add(db_contact)
        await db.flush()

        return db_contact

    @classmethod
    async def edit_customer_contact_dao(cls, db: AsyncSession, contact_id: int, contact: dict) -> None:
        """
        编辑联系人数据库操作

        :param db: orm 对象
        :param contact_id: 联系人 ID
        :param contact: 需要更新的联系人字典
        :return:
        """
        await db.execute(
            update(OaCustomerContact)
            .where(OaCustomerContact.id == contact_id)
            .values(**contact)
        )

    @classmethod
    async def del_customer_contact_dao(cls, db: AsyncSession, contact: CustomerContactModel) -> None:
        """
        删除联系人数据库操作（逻辑删除）

        :param db: orm 对象
        :param contact: 联系人对象
        :return:
        """
        update_time = contact.update_time if contact.update_time is not None else int(datetime.now().timestamp())
        delete_time = update_time
        await db.execute(
            update(OaCustomerContact)
            .where(OaCustomerContact.id.in_([contact.id]))
            .values(delete_time=delete_time, update_time=update_time)
        )

