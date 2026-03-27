from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_personnel.entity.do.admin_profile_do import OaAdminProfiles

from module_personnel.entity.vo.admin_profile_vo import OaAdminProfilesUpdateModel
from module_personnel.service.profile_service import ProfileService

profile_controller = APIRouterPro(
    prefix='/personnel/profile', order_num=3, tags=['人事管理-员工档案'], dependencies=[PreAuthDependency()]
)

@profile_controller.post(
    "/update",
    summary='更新个人信息',
    description='用于更新个人信息',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:profile:update')],
)
async def update_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaAdminProfilesUpdateModel,
)->Response:
    return await ProfileService().update_profile(query_db, model)

@profile_controller.get(
    "/detail/{admin_id}",
    summary='获取员工档案',
    description='用于获取员工档案',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:profile:uploadAvatar')],
)
async def get_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaAdminProfiles)],
    admin_id: int,
) -> Response:
    return await ProfileService.get_profile(query_db, admin_id, data_scope_sql)
