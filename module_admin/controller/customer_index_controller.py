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
        
        # 随机排序
        query = query.order_by(func.rand())
        
        # 分页
        offset = (page_num - 1) * page_size
        query = query.limit(page_size).offset(offset)
        
        result = await query_db.execute(query)
        customer_list = result.scalars().all()
        
        # 获取总数
        count_query = select(func.count(OaCustomer.id)).where(*conditions)
        count_result = await query_db.execute(count_query)
        total = count_result.scalar() or 0
        
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
            )
            for c in customer_list
        ]
        
        return ResponseUtil.success(
            data={
                'list': customers,
                'total': total,
                'page_num': page_num,
                'page_size': page_size
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
    industry_id: Annotated[int | None, Query(description='行业 ID')] = None,
    source_id: Annotated[int | None, Query(description='来源 ID')] = None,
    grade_id: Annotated[int | None, Query(description='等级 ID')] = None,
    follow_time_start: Annotated[int | None, Query(description='跟进时间开始')] = None,
    follow_time_end: Annotated[int | None, Query(description='跟进时间结束')] = None,
    page_num: Annotated[int, Query(description='页码')] = 1,
    page_size: Annotated[int, Query(description='每页数量')] = 10,
) -> Response:
    """公海客户列表"""
    try:
        # 基础查询条件：未删除、未废弃、无归属人
        conditions = [
            OaCustomer.delete_time == 0,
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
        
        # 分页
        offset = (page_num - 1) * page_size
        query = query.limit(page_size).offset(offset)
        
        result = await query_db.execute(query)
        customer_list = result.scalars().all()
        
        # 获取总数
        count_query = select(func.count(OaCustomer.id)).where(*conditions)
        count_result = await query_db.execute(count_query)
        total = count_result.scalar() or 0
        
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
            )
            for c in customer_list
        ]
        
        return ResponseUtil.success(
            data={
                'list': customers,
                'total': total,
                'page_num': page_num,
                'page_size': page_size
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
        
        # 分页
        offset = (page_num - 1) * page_size
        query = query.limit(page_size).offset(offset)
        
        result = await query_db.execute(query)
        customer_list = result.scalars().all()
        
        # 获取总数
        count_query = select(func.count(OaCustomer.id)).where(*conditions)
        count_result = await query_db.execute(count_query)
        total = count_result.scalar() or 0
        
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
        
        return ResponseUtil.success(
            data={
                'list': customers,
                'total': total,
                'page_num': page_num,
                'page_size': page_size
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
        
        # 批量更新（取消逻辑删除）
        for customer_id in id_array:
            await query_db.execute(
                update(OaCustomer)
                .where(OaCustomer.id == customer_id)
                .values(
                    delete_time=0,
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
