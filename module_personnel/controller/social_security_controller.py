# module_personnel/controller/social_security_controller.py
from fastapi import File, Form, Path, Query, Request, Response, UploadFile, Body
from typing import Annotated, List
from common.annotation.log_annotation import Log
from common.enums import BusinessType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_personnel.entity.do.social_security_do import OaSocialSecurity
from module_personnel.entity.vo.social_security_vo import (
    OaSocialSecurityBaseModel,
    OaSocialSecurityPageQueryModel,
    OaSocialSecurityUserPageQueryModel
)
from module_personnel.service.social_security_service import SocialSecurityService
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import CurrentUserModel

social_security_controller = APIRouterPro(
    prefix='/personnel/social_security', order_num=4, tags=['人事管理-社保管理'], dependencies=[PreAuthDependency()]
)

@social_security_controller.get(
    "/list",
    summary='获取社保信息列表',
    description='用于获取社保信息列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:list')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaSocialSecurityPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaSocialSecurity)],
) -> Response:
    result = await SocialSecurityService.get_page_list_service(query_db, query_object, data_scope_sql, True)
    return ResponseUtil.success(model_content=result)

@social_security_controller.post(
    "/add",
    summary='新增社保信息',
    description='用于新增社保信息',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:add')],
)
@Log(title='社保信息-新增', business_type=BusinessType.INSERT)
async def add_social_security(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaSocialSecurityBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 设置创建人信息
    query_object.create_by = current_user.user.user_name
    query_object.create_by_id = current_user.user.user_id
    result = await SocialSecurityService.add_or_update_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@social_security_controller.put(
    "/update",
    summary='更新社保信息',
    description='用于更新社保信息',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:update')],
)
@Log(title='社保信息-更新', business_type=BusinessType.UPDATE)
async def update_social_security(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaSocialSecurityBaseModel, Body()],
) -> Response:
    result = await SocialSecurityService.add_or_update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@social_security_controller.get(
    "/detail/{id}",
    summary='获取社保信息详情',
    description='用于获取社保信息详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:query')],
)
async def get_social_security_detail(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await SocialSecurityService.get_detail_service(query_db, id)
    return ResponseUtil.success(data=result)

@social_security_controller.put(
    "/terminate/{id}",
    summary='终止社保信息',
    description='用于终止社保信息',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:terminate')],
)
@Log(title='社保信息-终止', business_type=BusinessType.UPDATE)
async def terminate_social_security(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await SocialSecurityService.terminate_service(query_db, id)
    return ResponseUtil.success(msg=result.message)

@social_security_controller.delete(
    "/delete/{id}",
    summary='删除社保信息',
    description='用于删除社保信息',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:delete')],
)
@Log(title='社保信息-删除', business_type=BusinessType.DELETE)
async def delete_social_security(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result = await SocialSecurityService.delete_service(query_db, id)
    return ResponseUtil.success(msg=result.message)

@social_security_controller.get(
    "/users/list",
    summary='获取社保关联人员列表',
    description='用于获取社保关联人员列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:user:list')],
)
async def get_user_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaSocialSecurityUserPageQueryModel, Query()],
) -> Response:
    result = await SocialSecurityService.get_user_page_list_service(query_db, query_object, True)
    return ResponseUtil.success(dict_content=result)

@social_security_controller.post(
    "/user/add",
    summary='添加社保关联人员',
    description='用于添加社保关联人员，支持单个或批量添加（userId传入逗号分隔的ID字符串）',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:user:add')],
)
@Log(title='社保关联人员-添加', business_type=BusinessType.INSERT)
async def add_user(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    socialId: Annotated[int, Body(description='社保信息ID')],
    userId: Annotated[str, Body(description='员工ID（支持逗号分隔，如：3,14）')],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 解析逗号分隔的用户ID字符串
    user_ids = [int(u.strip()) for u in userId.split(',') if u.strip()]
    result = await SocialSecurityService.add_user_service(query_db, socialId, user_ids, current_user.user.user_id)
    if result.is_success:
        return ResponseUtil.success(msg=result.message)
    else:
        return ResponseUtil.failure(msg=result.message)

@social_security_controller.post(
    "/users/add",
    summary='批量添加社保关联人员',
    description='用于批量添加社保关联人员',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:user:add')],
)
@Log(title='社保关联人员-批量添加', business_type=BusinessType.INSERT)
async def batch_add_users(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    social_id: Annotated[int, Body(description='社保信息ID')],
    user_ids: Annotated[List[int], Body(description='员工ID列表')],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    result = await SocialSecurityService.batch_add_users_service(query_db, social_id, user_ids, current_user.user.user_id)
    return ResponseUtil.success(msg=result.message)

@social_security_controller.post(
    "/users/remove",
    summary='批量减员社保关联人员',
    description='用于批量减员社保关联人员',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:user:remove')],
)
@Log(title='社保关联人员-批量减员', business_type=BusinessType.UPDATE)
async def batch_remove_users(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    social_id: Annotated[int, Body(description='社保信息ID')],
    user_ids: Annotated[List[int], Body(description='员工ID列表')],
) -> Response:
    result = await SocialSecurityService.batch_remove_users_service(query_db, social_id, user_ids)
    return ResponseUtil.success(msg=result.message)

@social_security_controller.put(
    "/user/update",
    summary='修改用户社保关联信息',
    description='用于修改用户社保关联信息',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:user:update')],
)
@Log(title='社保关联人员-修改', business_type=BusinessType.UPDATE)
async def update_user(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: Annotated[int, Body(description='关联记录ID')],
    socialId: Annotated[int | None, Body(description='社保信息ID')] = None,
    userId: Annotated[int | None, Body(description='员工ID')] = None,
) -> Response:
    result = await SocialSecurityService.update_user_service(query_db, id, socialId, userId)
    if result.is_success:
        return ResponseUtil.success(msg=result.message)
    else:
        return ResponseUtil.failure(msg=result.message)

@social_security_controller.delete(
    "/user/remove",
    summary='删除用户社保关联信息',
    description='用于删除用户社保关联信息（减员），支持批量删除',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:user:remove')],
)
@Log(title='社保关联人员-删除', business_type=BusinessType.DELETE)
async def remove_user(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    socialId: Annotated[int, Body(description='社保信息ID')],
    userIds: Annotated[str, Body(description='用户ID列表（逗号分隔，如：1,2,3）')],
) -> Response:
    # 解析逗号分隔的用户ID字符串
    user_ids = [int(u.strip()) for u in userIds.split(',') if u.strip()]
    result = await SocialSecurityService.remove_user_service(query_db, socialId, user_ids)
    if result.is_success:
        return ResponseUtil.success(msg=result.message)
    else:
        return ResponseUtil.failure(msg=result.message)

@social_security_controller.post(
    "/users/import",
    summary='导入社保关联人员',
    description='用于导入社保关联人员',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:user:import')],
)
@Log(title='社保关联人员-导入', business_type=BusinessType.IMPORT)
async def import_users(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    social_id: Annotated[int, Form(description='社保信息ID')],
    file: Annotated[UploadFile, File(description='Excel文件')],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    file_content = await file.read()
    result = await SocialSecurityService.import_users_service(query_db, social_id, file_content, current_user.user.user_id)
    return ResponseUtil.success(msg=result.message)

@social_security_controller.get(
    "/reminder/expiring",
    summary='获取即将到期的社保信息',
    description='用于工作台显示即将到期的社保信息',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:reminder')],
)
async def get_expiring_reminder(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    days: Annotated[int, Query(description='天数，默认3天')] = 3,
) -> Response:
    result = await SocialSecurityService.get_expiring_reminder_service(query_db, days, current_user.user.user_id)
    return ResponseUtil.success(data=result)

@social_security_controller.get(
    "/reminder/expiring/count",
    summary='获取社保到期预警数量',
    description='根据当前日期计算，查询指定天数内即将到期的社保数量',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('personnel:social_security:reminder')],
)
async def get_expiring_count(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    days: Annotated[int, Query(description='预警天数，默认3天')] = 3,
) -> Response:
    result = await SocialSecurityService.get_expiring_count_service(query_db, days)
    return ResponseUtil.success(data=result)