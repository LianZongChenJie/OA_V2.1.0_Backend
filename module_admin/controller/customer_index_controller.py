from datetime import datetime
from typing import Annotated, Any
import random

from fastapi import Request, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import PageResponseModel
from module_admin.entity.do.customer_do import OaCustomer
from module_admin.entity.vo.customer_vo import CustomerModel
from utils.log_util import logger
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import CurrentUserModel

customer_index_controller = APIRouterPro(
    prefix='/customer/index', 
    order_num=99, 
    tags=['客户管理 - 抢客宝'],
    dependencies=[PreAuthDependency()]
)


@customer_index_controller.get(
    '/rush',
    summary='抢客宝接口',
    description='用于随机获取公海客户列表',
    response_model=PageResponseModel[CustomerModel],
    dependencies=[UserInterfaceAuthDependency('crm:customer:rush')],
)
async def rush_customer_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    page_num: Annotated[int, Query(description='页码')] = 1,
    page_size: Annotated[int, Query(description='每页数量')] = 10,
) -> Response:
    """抢客宝 - 随机获取公海客户"""
    try:
        # 查询条件：未删除、未废弃、无归属人的公海客户
        conditions = [
            OaCustomer.delete_time == 0,
            OaCustomer.discard_time == 0,
            OaCustomer.belong_uid == 0
        ]
        
        query = select(OaCustomer).where(*conditions)
        
        # 获取总数
        count_query = select(func.count(OaCustomer.id)).where(*conditions)
        count_result = await query_db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 随机排序
        query = query.order_by(func.rand())
        
        # 分页（兼容驼峰命名参数）
        final_page_num = pageNum if pageNum is not None else page_num
        final_page_size = pageSize if pageSize is not None else page_size
        offset = (final_page_num - 1) * final_page_size
        query = query.limit(final_page_size).offset(offset)
        
        result = await query_db.execute(query)
        customer_list = result.scalars().all()
        
        # 转换结果
        customers = [
            CustomerModel(
                id=c.id,
                name=c.name,
                source_id=c.source_id,
                grade_id=c.grade_id,
                industry_id=c.industry_id,
                address=c.address,
                content=c.content,
                market=c.market,
                create_time=c.create_time,
                belong_uid=c.belong_uid,
                belong_did=c.belong_did,
                belong_time=c.belong_time,
                delete_time=c.delete_time,
            )
            for c in customer_list
        ]
        
        # 计算是否有下一页
        has_next = (page_num * page_size) < total
        
        return ResponseUtil.success(
            rows=[customer.model_dump(by_alias=True) for customer in customers],
            dict_content={
                'pageNum': page_num,
                'pageSize': page_size,
                'total': total,
                'hasNext': has_next
            }
        )
    except Exception as e:
        logger.error(f'抢客宝获取失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=str(e))


@customer_index_controller.get(
    '/rush/limit',
    summary='获取抢客宝限制信息',
    description='获取每日抢客数量限制和已抢数量',
    dependencies=[UserInterfaceAuthDependency('crm:customer:rush')],
)
async def get_rush_limit_info(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """获取抢客宝限制信息"""
    try:
        # 获取每日最大抢客数配置
        today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        
        # 查询今日已抢客户数
        count_query = select(func.count(OaCustomer.id)).where(
            OaCustomer.belong_time > today_start,
            OaCustomer.belong_uid == current_user.user.user_id
        )
        count_result = await query_db.execute(count_query)
        today_count = count_result.scalar() or 0
        
        # TODO: 从配置表获取限制数量（需要从 DataAuth 表迁移配置）
        max_num_per_day = 10  # 默认值
        
        return ResponseUtil.success(data={
            'max_num': max_num_per_day,
            'count': today_count
        })
    except Exception as e:
        logger.error(f'获取抢客限制失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=str(e))


@customer_index_controller.get(
    '/sea',
    summary='公海客户列表接口',
    description='用于获取公海客户列表（支持搜索过滤）',
    response_model=PageResponseModel[CustomerModel],
    dependencies=[UserInterfaceAuthDependency('crm:customer:sea')],
)
async def sea_customer_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    keywords: Annotated[str | None, Query(description='搜索关键词')] = None,
    name: Annotated[str | None, Query(description='客户名称')] = None,
    industry_id: Annotated[int | None, Query(alias='industryId', description='行业 ID')] = None,
    source_id: Annotated[int | None, Query(alias='sourceId', description='来源 ID')] = None,
    grade_id: Annotated[int | None, Query(alias='gradeId', description='等级 ID')] = None,
    customer_status: Annotated[int | None, Query(alias='customerStatus', description='客户状态')] = None,
    intent_status: Annotated[int | None, Query(alias='intentStatus', description='意向状态')] = None,
    follow_time_start: Annotated[int | None, Query(description='跟进时间开始')] = None,
    follow_time_end: Annotated[int | None, Query(description='跟进时间结束')] = None,
    page_num: Annotated[int, Query(alias='pageNum', description='页码')] = 1,
    page_size: Annotated[int, Query(alias='pageSize', description='每页数量')] = 10,
) -> Response:
    """公海客户列表"""
    try:
        from module_basicdata.dao.custom.customer_gradle_dao import CustomerGradleDao
        from module_basicdata.dao.custom.customer_source_dao import CustomerSourceDao
        from module_basicdata.dao.custom.industry_dao import IndustryDao
        from module_admin.entity.do.customer_contact_do import OaCustomerContact
        from utils.time_format_util import timestamp_to_datetime
        from utils.common_util import CamelCaseUtil
        
        # 状态映射
        status_map = {0: '未设置', 1: '待跟进', 2: '跟进中', 3: '已成交', 4: '已流失'}
        intent_map = {0: '未设置', 1: '低', 2: '中', 3: '高', 4: '极高'}
        
        # 基础查询条件：未删除、未废弃、无归属人
        conditions = [
            OaCustomer.delete_time == 0,
            OaCustomer.discard_time == 0,
            OaCustomer.belong_uid == 0
        ]
        
        # 关键词搜索（优先使用 name，兼容 keywords）
        search_keywords = name if name else keywords
        if search_keywords:
            conditions.append(
                or_(
                    OaCustomer.id.like(f'%{search_keywords}%'),
                    OaCustomer.name.like(f'%{search_keywords}%')
                )
            )
        
        # 行业过滤
        if industry_id is not None:
            conditions.append(OaCustomer.industry_id == industry_id)
        
        # 来源过滤
        if source_id is not None:
            conditions.append(OaCustomer.source_id == source_id)
        
        # 等级过滤
        if grade_id is not None:
            conditions.append(OaCustomer.grade_id == grade_id)
        
        # 客户状态过滤
        if customer_status is not None:
            conditions.append(OaCustomer.customer_status == customer_status)
        
        # 意向状态过滤
        if intent_status is not None:
            conditions.append(OaCustomer.intent_status == intent_status)
        
        # 跟进时间范围过滤
        if follow_time_start is not None and follow_time_end is not None:
            conditions.append(
                and_(
                    OaCustomer.follow_time >= follow_time_start,
                    OaCustomer.follow_time <= follow_time_end
                )
            )
        
        query = select(OaCustomer).where(*conditions)
        query = query.order_by(OaCustomer.create_time.desc())
        
        # 获取总数
        count_query = select(func.count(OaCustomer.id)).where(*conditions)
        count_result = await query_db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 分页
        offset = (page_num - 1) * page_size
        query = query.limit(page_size).offset(offset)
        
        result = await query_db.execute(query)
        customer_list = result.scalars().all()
        
        # 转换结果，添加扩展信息
        customers = []
        for c in customer_list:
            customer_dict = {
                'id': c.id,
                'name': c.name,
                'source_id': c.source_id,
                'grade_id': c.grade_id,
                'industry_id': c.industry_id,
                'services_id': c.services_id,
                'provinceid': c.provinceid,
                'cityid': c.cityid,
                'distid': c.distid,
                'townid': c.townid,
                'address': c.address,
                'customer_status': c.customer_status,
                'intent_status': c.intent_status,
                'contact_first': c.contact_first,
                'admin_id': c.admin_id,
                'belong_uid': c.belong_uid,
                'belong_did': c.belong_did,
                'belong_time': c.belong_time,
                'distribute_time': c.distribute_time,
                'follow_time': c.follow_time,
                'next_time': c.next_time,
                'discard_time': c.discard_time,
                'share_ids': c.share_ids,
                'content': c.content,
                'market': c.market,
                'remark': c.remark,
                'tax_bank': c.tax_bank,
                'tax_banksn': c.tax_banksn,
                'tax_num': c.tax_num,
                'tax_mobile': c.tax_mobile,
                'tax_address': c.tax_address,
                'is_lock': c.is_lock,
                'create_time': c.create_time,
                'update_time': c.update_time,
                'delete_time': c.delete_time,
            }
            
            # 获取行业名称
            if c.industry_id and int(c.industry_id) > 0:
                industry_info = await IndustryDao.get_industry_info(query_db, int(c.industry_id))
                customer_dict['industry'] = industry_info.title if industry_info else None
            
            # 获取等级名称
            if c.grade_id and int(c.grade_id) > 0:
                grade_info = await CustomerGradleDao.get_info_by_id(query_db, int(c.grade_id))
                customer_dict['grade'] = grade_info.title if grade_info else None
            
            # 获取来源名称
            if c.source_id and int(c.source_id) > 0:
                source_info = await CustomerSourceDao.get_info_by_id(query_db, int(c.source_id))
                customer_dict['source'] = source_info.title if source_info else None
            
            # 获取客户状态名称
            if c.customer_status is not None:
                customer_dict['customer_status_name'] = status_map.get(int(c.customer_status), '未知')
            else:
                customer_dict['customer_status_name'] = '未设置'
            
            # 获取意向状态名称
            if c.intent_status is not None:
                customer_dict['intent_status_name'] = intent_map.get(int(c.intent_status), '未知')
            else:
                customer_dict['intent_status_name'] = '未设置'
            
            # 获取第一联系人信息
            if c.contact_first and int(c.contact_first) > 0:
                contact_query = select(OaCustomerContact).where(
                    OaCustomerContact.id == c.contact_first,
                    OaCustomerContact.delete_time == 0
                )
                contact_result = await query_db.execute(contact_query)
                contact_info = contact_result.scalars().first()
                if contact_info:
                    customer_dict['contact_name'] = contact_info.name
                    customer_dict['contact_mobile'] = contact_info.mobile
                    customer_dict['contact_email'] = contact_info.email
            
            # 获取所属员工和所属部门（公海客户通常为空，显示'未分配'）
            if c.belong_uid and int(c.belong_uid) > 0:
                from module_admin.entity.do.user_do import OaUser
                user_query = select(OaUser).where(OaUser.user_id == c.belong_uid)
                user_result = await query_db.execute(user_query)
                user_info = user_result.scalars().first()
                if user_info:
                    customer_dict['belong_name'] = user_info.nick_name
            else:
                customer_dict['belong_name'] = '未分配'
            
            if c.belong_did and int(c.belong_did) > 0:
                from module_admin.entity.do.dept_do import OaDept
                dept_query = select(OaDept).where(OaDept.dept_id == c.belong_did)
                dept_result = await query_db.execute(dept_query)
                dept_info = dept_result.scalars().first()
                if dept_info:
                    customer_dict['belong_department'] = dept_info.dept_name
            else:
                customer_dict['belong_department'] = '未分配'
            
            # 格式化时间
            if c.create_time and int(c.create_time) > 0:
                customer_dict['create_time_str'] = timestamp_to_datetime(int(c.create_time), '%Y-%m-%d %H:%M:%S')
            if c.belong_time and int(c.belong_time) > 0:
                customer_dict['belong_time_str'] = timestamp_to_datetime(int(c.belong_time), '%Y-%m-%d %H:%M:%S')
            if c.follow_time and int(c.follow_time) > 0:
                customer_dict['follow_time_str'] = timestamp_to_datetime(int(c.follow_time), '%Y-%m-%d %H:%M:%S')
            if c.next_time and int(c.next_time) > 0:
                customer_dict['next_time_str'] = timestamp_to_datetime(int(c.next_time), '%Y-%m-%d %H:%M:%S')
            if c.distribute_time and int(c.distribute_time) > 0:
                customer_dict['distribute_time_str'] = timestamp_to_datetime(int(c.distribute_time), '%Y-%m-%d %H:%M:%S')
            if c.update_time and int(c.update_time) > 0:
                customer_dict['update_time_str'] = timestamp_to_datetime(int(c.update_time), '%Y-%m-%d %H:%M:%S')
            
            # 转换为驼峰命名
            customer_dict = CamelCaseUtil.transform_result(customer_dict)
            customers.append(customer_dict)
        
        # 计算是否有下一页
        has_next = (page_num * page_size) < total
        
        return ResponseUtil.success(
            rows=customers,
            dict_content={
                'pageNum': page_num,
                'pageSize': page_size,
                'total': total,
                'hasNext': has_next
            }
        )
    except Exception as e:
        logger.error(f'公海客户列表获取失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=str(e))


@customer_index_controller.get(
    '/trash',
    summary='废弃池客户列表接口',
    description='用于获取废弃池客户列表（支持搜索过滤）',
    response_model=PageResponseModel[CustomerModel],
    dependencies=[UserInterfaceAuthDependency('crm:customer:trash')],
)
async def trash_customer_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    keywords: Annotated[str | None, Query(description='搜索关键词')] = None,
    industry_id: Annotated[int | None, Query(description='行业 ID')] = None,
    source_id: Annotated[int | None, Query(description='来源 ID')] = None,
    grade_id: Annotated[int | None, Query(description='等级 ID')] = None,
    page_num: Annotated[int, Query(description='页码')] = 1,
    page_size: Annotated[int, Query(description='每页数量')] = 10,
) -> Response:
    """废弃池客户列表"""
    try:
        # 基础查询条件：已逻辑删除、无归属人
        conditions = [
            OaCustomer.delete_time > 0,
            OaCustomer.discard_time == 0,
            OaCustomer.belong_uid == 0
        ]
        
        # 关键词搜索
        if keywords:
            conditions.append(
                or_(
                    OaCustomer.id.like(f'%{keywords}%'),
                    OaCustomer.name.like(f'%{keywords}%')
                )
            )
        
        # 行业过滤
        if industry_id is not None:
            conditions.append(OaCustomer.industry_id == industry_id)
        
        # 来源过滤
        if source_id is not None:
            conditions.append(OaCustomer.source_id == source_id)
        
        # 等级过滤
        if grade_id is not None:
            conditions.append(OaCustomer.grade_id == grade_id)
        
        query = select(OaCustomer).where(*conditions)
        query = query.order_by(OaCustomer.delete_time.desc())
        
        # 获取总数
        count_query = select(func.count(OaCustomer.id)).where(*conditions)
        count_result = await query_db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 分页
        offset = (page_num - 1) * page_size
        query = query.limit(page_size).offset(offset)
        
        result = await query_db.execute(query)
        customer_list = result.scalars().all()
        
        # 转换结果
        customers = [
            CustomerModel(
                id=c.id,
                name=c.name,
                source_id=c.source_id,
                grade_id=c.grade_id,
                industry_id=c.industry_id,
                address=c.address,
                content=c.content,
                market=c.market,
                create_time=c.create_time,
                delete_time=c.delete_time,
                belong_uid=c.belong_uid,
                belong_did=c.belong_did,
            )
            for c in customer_list
        ]
        
        # 计算是否有下一页
        has_next = (page_num * page_size) < total
        
        return ResponseUtil.success(
            rows=[customer.model_dump(by_alias=True) for customer in customers],
            dict_content={
                'pageNum': page_num,
                'pageSize': page_size,
                'total': total,
                'hasNext': has_next
            }
        )
    except Exception as e:
        logger.error(f'废弃池客户列表获取失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=str(e))


@customer_index_controller.post(
    '/to-sea',
    summary='移入公海接口',
    description='将客户移入公海池（清空归属人和归属部门）',
    dependencies=[UserInterfaceAuthDependency('crm:customer:to-sea')],
)
@Log(title='客户管理', business_type=BusinessType.UPDATE)
async def move_to_sea(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ids: Annotated[str, Query(description='客户 ID 列表，逗号分隔')] = '',
) -> Response:
    """将客户移入公海"""
    try:
        if not ids:
            raise ValueError('客户 ID 不能为空')
        
        id_array = [int(id.strip()) for id in ids.split(',') if id.strip()]
        
        current_time = int(datetime.now().timestamp())
        
        # 批量更新
        for customer_id in id_array:
            await query_db.execute(
                update(OaCustomer)
                .where(OaCustomer.id == customer_id)
                .values(
                    belong_uid=0,
                    belong_did=0,
                    belong_time=0,
                    update_time=current_time
                )
            )
            
            # TODO: 添加操作日志
            logger.info(f'客户{customer_id}已移入公海')
        
        await query_db.commit()
        
        return ResponseUtil.success(msg='操作成功')
    except Exception as e:
        await query_db.rollback()
        logger.error(f'移入公海失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=str(e))


@customer_index_controller.post(
    '/to-get',
    summary='领取客户接口',
    description='从公海领取客户（设置归属人和归属部门）',
    dependencies=[UserInterfaceAuthDependency('crm:customer:get')],
)
@Log(title='客户管理', business_type=BusinessType.UPDATE)
async def get_customer(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    id: Annotated[int, Query(description='客户 ID')] = 0,
) -> Response:
    """领取客户"""
    try:
        if not id:
            raise ValueError('客户 ID 不能为空')
        
        # 获取每日最大领取数配置
        today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        
        # 查询今日已领取客户数
        count_query = select(func.count(OaCustomer.id)).where(
            OaCustomer.belong_time >= today_start,
            OaCustomer.belong_uid == current_user.user.user_id
        )
        count_result = await query_db.execute(count_query)
        today_count = count_result.scalar() or 0
        
        # TODO: 从配置表获取限制数量
        max_num_per_day = 10  # 默认值
        
        if today_count >= max_num_per_day:
            raise ValueError('今日领取客户数已到达上限，请明天再来领取')
        
        # 查询个人总客户数限制
        total_count_query = select(func.count(OaCustomer.id)).where(
            OaCustomer.belong_uid == current_user.user.user_id
        )
        total_count_result = await query_db.execute(total_count_query)
        total_count = total_count_result.scalar() or 0
        
        max_num_total = 50  # 默认值
        
        if total_count >= max_num_total:
            raise ValueError('领取客户数已到达上限，请把部分客户移到公海里再来领取')
        
        # 更新客户归属
        current_time = int(datetime.now().timestamp())
        await query_db.execute(
            update(OaCustomer)
            .where(OaCustomer.id == id)
            .values(
                belong_uid=current_user.user.user_id,
                belong_did=current_user.user.dept_id,
                belong_time=current_time,
                update_time=current_time
            )
        )
        
        await query_db.commit()
        
        # TODO: 添加操作日志
        logger.info(f'客户{id}已被领取')
        
        return ResponseUtil.success(msg='操作成功')
    except Exception as e:
        await query_db.rollback()
        logger.error(f'领取客户失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=str(e))


@customer_index_controller.post(
    '/to-trash',
    summary='移入废弃池接口',
    description='将客户移入废弃池（逻辑删除）',
    dependencies=[UserInterfaceAuthDependency('crm:customer:to-trash')],
)
@Log(title='客户管理', business_type=BusinessType.DELETE)
async def move_to_trash(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ids: Annotated[str, Query(description='客户 ID 列表，逗号分隔')] = '',
) -> Response:
    """将客户移入废弃池"""
    try:
        if not ids:
            raise ValueError('客户 ID 不能为空')
        
        id_array = [int(id.strip()) for id in ids.split(',') if id.strip()]
        
        current_time = int(datetime.now().timestamp())
        
        # 批量更新（逻辑删除）
        for customer_id in id_array:
            await query_db.execute(
                update(OaCustomer)
                .where(OaCustomer.id == customer_id)
                .values(
                    delete_time=current_time,
                    update_time=current_time
                )
            )
            
            # TODO: 添加操作日志
            logger.info(f'客户{customer_id}已移入废弃池')
        
        await query_db.commit()
        
        return ResponseUtil.success(msg='操作成功')
    except Exception as e:
        await query_db.rollback()
        logger.error(f'移入废弃池失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=str(e))


@customer_index_controller.post(
    '/to-revert',
    summary='还原客户接口',
    description='从废弃池还原客户（取消逻辑删除）',
    dependencies=[UserInterfaceAuthDependency('crm:customer:revert')],
)
@Log(title='客户管理', business_type=BusinessType.UPDATE)
async def revert_customer(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    ids: Annotated[str, Query(description='客户 ID 列表，逗号分隔')] = '',
) -> Response:
    """还原客户"""
    try:
        if not ids:
            raise ValueError('客户 ID 不能为空')
        
        id_array = [int(id.strip()) for id in ids.split(',') if id.strip()]
        
        current_time = int(datetime.now().timestamp())

        # 批量更新（取消逻辑删除和废弃状态，同时清空归属信息使其回到公海）
        for customer_id in id_array:
            await query_db.execute(
                update(OaCustomer)
                .where(OaCustomer.id == customer_id)
                .values(
                    delete_time=0,
                    discard_time=0,  # 同时取消废弃状态
                    belong_uid=0,     # 清空归属人，使其回到公海
                    belong_did=0,     # 清空归属部门
                    belong_time=0,    # 清空归属时间
                    update_time=current_time
                )
            )

        # TODO: 添加操作日志
        logger.info(f'客户{customer_id}已还原')
        
        await query_db.commit()
        
        return ResponseUtil.success(msg='操作成功')
    except Exception as e:
        await query_db.rollback()
        logger.error(f'还原客户失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=str(e))