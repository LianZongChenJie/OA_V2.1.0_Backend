from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.customer_do import OaCustomer
from module_admin.entity.vo.customer_vo import CustomerModel, CustomerPageQueryModel
from utils.page_util import PageUtil
from utils.time_format_util import timestamp_to_datetime
from utils.log_util import logger


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
        from module_admin.entity.do.customer_contact_do import OaCustomerContact
        
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
            'share_names': '',
            'contact_list': [],
        }

        try:
            contact_query = (
                select(OaCustomerContact)
                .where(
                    and_(
                        OaCustomerContact.cid == customer_id,
                        OaCustomerContact.delete_time == 0
                    )
                )
                .order_by(OaCustomerContact.is_default.desc(), OaCustomerContact.id.asc())
            )
            contact_rows = (await db.execute(contact_query)).scalars().all()
            
            contact_list = []
            first_contact = None
            for contact in contact_rows:
                contact_dict = {
                    'id': contact.id,
                    'cid': contact.cid,
                    'isDefault': contact.is_default,
                    'name': contact.name or '',
                    'sex': contact.sex if contact.sex is not None else 0,
                    'mobile': contact.mobile or '',
                    'qq': contact.qq or '',
                    'wechat': contact.wechat or '',
                    'email': contact.email or '',
                    'nickname': contact.nickname or '',
                    'department': contact.department or '',
                    'position': contact.position or '',
                    'birthday': contact.birthday or '',
                    'address': contact.address or '',
                    'family': contact.family or '',
                    'adminId': contact.admin_id,
                    'createTime': contact.create_time,
                    'updateTime': contact.update_time,
                    'deleteTime': contact.delete_time,
                }
                contact_list.append(contact_dict)
                
                if contact.is_default == 1 and first_contact is None:
                    first_contact = contact
            
            result['contact_list'] = contact_list
            
            if first_contact:
                result['contact_name'] = first_contact.name
                result['contact_mobile'] = first_contact.mobile
                result['contact_email'] = first_contact.email
            elif contact_list:
                first = contact_list[0]
                result['contact_name'] = first.get('name')
                result['contact_mobile'] = first.get('mobile')
                result['contact_email'] = first.get('email')
        except Exception as e:
            logger.error(f'查询联系人信息失败: {e}')

        try:
            belong_uid = customer_info.belong_uid
            if belong_uid and int(belong_uid) > 0:
                from module_admin.dao.user_dao import UserDao
                user_result = await UserDao.get_user_by_id(db, int(belong_uid))
                if user_result and user_result.get('user_basic_info'):
                    user_info = user_result['user_basic_info']
                    result['belong_name'] = user_info.nick_name or user_info.user_name or ''
        except Exception as e:
            logger.error(f'查询所属人失败: {e}')

        try:
            belong_did = customer_info.belong_did
            if belong_did and int(belong_did) > 0:
                from module_admin.dao.dept_dao import DeptDao
                dept_info = await DeptDao.get_dept_detail_by_id(db, int(belong_did))
                if dept_info:
                    result['belong_department'] = dept_info.dept_name or ''
        except Exception as e:
            logger.error(f'查询所属部门失败: {e}')

        try:
            grade_id = customer_info.grade_id
            if grade_id and int(grade_id) > 0:
                from module_basicdata.dao.custom.customer_gradle_dao import CustomerGradleDao
                grade_info = await CustomerGradleDao.get_info_by_id(db, int(grade_id))
                if grade_info:
                    result['grade'] = grade_info.title or ''
        except Exception as e:
            logger.error(f'查询客户等级失败: {e}')

        try:
            source_id = customer_info.source_id
            if source_id and int(source_id) > 0:
                from module_basicdata.dao.custom.customer_source_dao import CustomerSourceDao
                source_info = await CustomerSourceDao.get_info_by_id(db, int(source_id))
                if source_info:
                    result['source'] = source_info.title or ''
        except Exception as e:
            logger.error(f'查询客户来源失败: {e}')

        try:
            industry_id = customer_info.industry_id
            if industry_id and int(industry_id) > 0:
                from module_basicdata.dao.custom.industry_dao import IndustryDao
                industry_info = await IndustryDao.get_industry_info(db, int(industry_id))
                if industry_info:
                    result['industry'] = industry_info.title or ''
        except Exception as e:
            logger.error(f'查询行业失败: {e}')

        try:
            customer_status = customer_info.customer_status
            if customer_status is not None:
                status_map = {0: '未设置', 1: '潜在客户', 2: '意向客户', 3: '正式客户', 4: '流失客户'}
                result['customer_status_name'] = status_map.get(int(customer_status), '未知')
            else:
                result['customer_status_name'] = '未设置'
        except Exception as e:
            logger.error(f'处理客户状态失败: {e}')

        try:
            intent_status = customer_info.intent_status
            if intent_status is not None:
                intent_map = {0: '未设置', 1: '高意向', 2: '中意向', 3: '低意向', 4: '无意向', 10: '未知'}
                result['intent_status_name'] = intent_map.get(int(intent_status), '未知')
            else:
                result['intent_status_name'] = '未设置'
        except Exception as e:
            logger.error(f'处理意向状态失败: {e}')

        try:
            share_ids = customer_info.share_ids
            if share_ids:
                from module_admin.dao.user_dao import UserDao
                share_id_list = [int(sid.strip()) for sid in share_ids.split(',') if sid.strip()]
                share_names = []
                for sid in share_id_list:
                    user_result = await UserDao.get_user_by_id(db, sid)
                    if user_result and user_result.get('user_basic_info'):
                        user_info = user_result['user_basic_info']
                        share_names.append(user_info.nick_name or user_info.user_name or '')
                result['share_names'] = ','.join(share_names) if share_names else ''
        except Exception as e:
            logger.error(f'查询共享人员失败: {e}')

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

        # 处理列表数据，添加扩展字段
        if isinstance(customer_list, PageModel) and hasattr(customer_list, 'rows'):
            processed_rows = []
            for row in customer_list.rows:
                item = await cls._process_customer_row(db, row)
                processed_rows.append(item)
            customer_list.rows = processed_rows
        elif isinstance(customer_list, list):
            processed_list = []
            for row in customer_list:
                item = await cls._process_customer_row(db, row)
                processed_list.append(item)
            customer_list = processed_list

        return customer_list

    @classmethod
    async def _process_customer_row(cls, db: AsyncSession, row: Any) -> dict[str, Any]:
        """
        处理客户行数据，添加扩展字段

        :param db: orm 对象
        :param row: 客户行数据
        :return: 处理后的字典数据
        """
        from utils.camel_converter import ModelConverter
        
        if not isinstance(row, dict):
            if hasattr(row, '__table__'):
                row = ModelConverter.to_dict(row, by_alias=True)
            else:
                return row

        result = row.copy()

        # 初始化扩展字段
        result['belongName'] = None
        result['belongDepartment'] = None
        result['industry'] = None
        result['grade'] = None
        result['source'] = None
        result['customerStatusName'] = None
        result['intentStatusName'] = None
        result['followTimeStr'] = None
        result['nextTimeStr'] = None
        result['createTimeStr'] = None
        result['contactName'] = None
        result['contactMobile'] = None
        result['contactEmail'] = None

        # 查询所属人姓名
        belong_uid = row.get('belongUid')
        if belong_uid and int(belong_uid) > 0:
            from module_admin.dao.user_dao import UserDao
            user_result = await UserDao.get_user_by_id(db, int(belong_uid))
            if user_result and user_result.get('user_basic_info'):
                user_info = user_result['user_basic_info']
                result['belongName'] = user_info.nick_name or user_info.user_name

        # 查询所属部门名称
        belong_did = row.get('belongDid')
        if belong_did and int(belong_did) > 0:
            from module_admin.dao.dept_dao import DeptDao
            dept_info = await DeptDao.get_dept_detail_by_id(db, int(belong_did))
            if dept_info:
                result['belongDepartment'] = dept_info.dept_name

        # 查询客户等级
        grade_id = row.get('gradeId')
        if grade_id and int(grade_id) > 0:
            from module_basicdata.dao.custom.customer_gradle_dao import CustomerGradleDao
            try:
                grade_info = await CustomerGradleDao.get_info_by_id(db, int(grade_id))
                if grade_info:
                    result['grade'] = grade_info.title
            except Exception as e:
                logger.error(f'查询客户等级失败: {e}')

        # 查询来源渠道
        source_id = row.get('sourceId')
        if source_id and int(source_id) > 0:
            from module_basicdata.dao.custom.customer_source_dao import CustomerSourceDao
            try:
                source_info = await CustomerSourceDao.get_info_by_id(db, int(source_id))
                if source_info:
                    result['source'] = source_info.title
            except Exception as e:
                logger.error(f'查询客户来源失败: {e}')

        # 查询所属行业
        industry_id = row.get('industryId')
        if industry_id and int(industry_id) > 0:
            from module_basicdata.dao.custom.industry_dao import IndustryDao
            try:
                industry_info = await IndustryDao.get_industry_info(db, int(industry_id))
                if industry_info:
                    result['industry'] = industry_info.title
            except Exception as e:
                logger.error(f'查询行业失败: {e}')

        # 查询第一联系人信息
        contact_first = row.get('contactFirst')
        if contact_first and int(contact_first) > 0:
            from module_admin.entity.do.customer_contact_do import OaCustomerContact
            try:
                query = select(OaCustomerContact).where(OaCustomerContact.id == int(contact_first))
                contact_info = (await db.execute(query)).scalars().first()
                if contact_info:
                    result['contactName'] = contact_info.name
                    result['contactMobile'] = contact_info.mobile
                    result['contactEmail'] = contact_info.email
            except Exception as e:
                logger.error(f'查询联系人失败: {e}')

        # 格式化时间字段
        follow_time = row.get('followTime')
        if follow_time and int(follow_time) > 0:
            result['followTimeStr'] = timestamp_to_datetime(int(follow_time), '%Y-%m-%d %H:%M:%S')

        next_time = row.get('nextTime')
        if next_time and int(next_time) > 0:
            result['nextTimeStr'] = timestamp_to_datetime(int(next_time), '%Y-%m-%d %H:%M:%S')

        create_time = row.get('createTime')
        if create_time and int(create_time) > 0:
            result['createTimeStr'] = timestamp_to_datetime(int(create_time), '%Y-%m-%d %H:%M:%S')

        belong_time = row.get('belongTime')
        if belong_time and int(belong_time) > 0:
            result['belongTimeStr'] = timestamp_to_datetime(int(belong_time), '%Y-%m-%d %H:%M:%S')

        distribute_time = row.get('distributeTime')
        if distribute_time and int(distribute_time) > 0:
            result['distributeTimeStr'] = timestamp_to_datetime(int(distribute_time), '%Y-%m-%d %H:%M:%S')

        update_time = row.get('updateTime')
        if update_time and int(update_time) > 0:
            result['updateTimeStr'] = timestamp_to_datetime(int(update_time), '%Y-%m-%d %H:%M:%S')

        # 客户状态名称
        customer_status = row.get('customerStatus')
        if customer_status is not None:
            status_map = {0: '未设置', 1: '潜在客户', 2: '意向客户', 3: '正式客户', 4: '流失客户'}
            result['customerStatusName'] = status_map.get(int(customer_status), '未知')

        # 意向状态名称
        intent_status = row.get('intentStatus')
        if intent_status is not None:
            intent_map = {0: '未设置', 1: '高意向', 2: '中意向', 3: '低意向', 4: '无意向'}
            result['intentStatusName'] = intent_map.get(int(intent_status), '未知')

        return result

    @classmethod
    async def add_customer_dao(cls, db: AsyncSession, customer_data: dict) -> OaCustomer:
        """
        新增客户数据库操作

        :param db: orm 对象
        :param customer_data: 客户数据字典
        :return:
        """
        db_customer = OaCustomer(**customer_data)
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



    @classmethod
    async def get_customer_count(cls, db: AsyncSession) -> OaCustomer | None:
        query = select(func.count()).select_from(OaCustomer).where(OaCustomer.delete_time == 0)
        count = await db.execute(query)
        return count.scalar()
