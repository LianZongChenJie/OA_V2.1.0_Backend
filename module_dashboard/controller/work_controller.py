from fastapi import File, Form, Path, Query, Request, Response, UploadFile, Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_dashboard.entity.do.work_do import OaWork
from module_dashboard.entity.vo.work_vo import OaWorkBaseModel, OaWorkPageQueryModel, OaWorkQueryModel
from module_dashboard.service.work_service import WorkService
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)
from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil
from common.annotation.log_annotation import Log
from common.enums import BusinessType
from utils.log_util import logger
from exceptions.exception import ServiceException

dashboard_work_controller = APIRouterPro(
    prefix='/oa/work', order_num=4, tags=['个人办公-工作汇报'], dependencies=[PreAuthDependency()]
)

@dashboard_work_controller.get(
    "/datalist",
    summary='获取工作汇报列表',
    description='用于获取工作汇报分页列表（我发出的或我接收的）',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:work:list')],
)
async def get_work_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaWorkPageQueryModel, Query()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaWork)],
) -> Response:
    """
    获取工作汇报列表
    send=1: 我发出的汇报
    send=0: 我接收的汇报
    """
    try:
        query_object.admin_id = current_user.user.user_id
        
        if query_object.send == 1:
            result = await WorkService.get_send_list_service(query_db, query_object, data_scope_sql, False)
        else:
            result = await WorkService.get_accept_list_service(query_db, query_object, data_scope_sql, False)
        
        logger.info('获取工作汇报列表成功')
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        logger.error(f'获取工作汇报列表失败：{e.message}', exc_info=True)
        return ResponseUtil.error(msg=e.message or '操作失败')
    except Exception as e:
        logger.exception(f'获取工作汇报列表失败：{str(e)}')
        return ResponseUtil.error(msg=str(e) or '系统内部错误，请联系管理员')

@dashboard_work_controller.post(
    "/add",
    summary='新增/编辑工作汇报',
    description='用于新增或编辑工作汇报，支持草稿和发送',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:work:add')],
)
@Log(title='工作汇报', business_type=BusinessType.INSERT)
async def add_work(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaWorkQueryModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    新增或编辑工作汇报
    - id=0: 新增
    - id>0: 编辑
    - is_send=true: 发送汇报
    - is_send=false: 保存草稿
    """
    try:
        if query_object.id and query_object.id > 0:
            result = await WorkService.update_service(query_db, query_object, current_user.user.user_id)
        else:
            result = await WorkService.add_service(query_db, query_object, current_user.user.user_id)
        
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        logger.error(f'保存工作汇报失败：{e.message}', exc_info=True)
        return ResponseUtil.error(msg=e.message or '操作失败')
    except Exception as e:
        logger.exception(f'保存工作汇报失败：{str(e)}')
        return ResponseUtil.error(msg=str(e) or '系统内部错误，请联系管理员')

@dashboard_work_controller.get(
    "/view/{id}",
    summary='查看工作汇报详情',
    description='用于查看工作汇报详细信息，自动标记已读',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:work:query')],
)
async def view_work(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    查看工作汇报详情
    - 如果是接收人查看，自动标记为已读
    - 如果是创建人查看，返回已读人列表
    """
    try:
        result = await WorkService.get_info_service(query_db, id, current_user.user.user_id)
        logger.info(f'查看工作汇报详情成功，ID: {id}')
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        logger.error(f'查看工作汇报详情失败：{e.message}', exc_info=True)
        return ResponseUtil.error(msg=e.message or '操作失败')
    except Exception as e:
        logger.exception(f'查看工作汇报详情失败：{str(e)}')
        return ResponseUtil.error(msg=str(e) or '系统内部错误，请联系管理员')

@dashboard_work_controller.delete(
    "/del/{id}",
    summary='删除工作汇报',
    description='用于删除工作汇报（仅创建人可删除）',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:work:delete')],
)
@Log(title='工作汇报', business_type=BusinessType.DELETE)
async def delete_work(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    删除工作汇报
    - 仅创建人可以删除
    - 同时删除相关的发送记录
    """
    try:
        result = await WorkService.del_by_id(query_db, id, current_user.user.user_id)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        logger.error(f'删除工作汇报失败：{e.message}', exc_info=True)
        return ResponseUtil.error(msg=e.message or '操作失败')
    except Exception as e:
        logger.exception(f'删除工作汇报失败：{str(e)}')
        return ResponseUtil.error(msg=str(e) or '系统内部错误，请联系管理员')
