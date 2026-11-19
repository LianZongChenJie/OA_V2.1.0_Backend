import io
import urllib.parse
from datetime import datetime
from typing import Annotated

from fastapi import File, Path, Query, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_project_monthly.entity.vo.project_monthly_vo import (
    AddProjectMonthlyModel,
    DeleteProjectMonthlyModel,
    EditProjectMonthlyModel,
    ProjectMonthlyImportResponseModel,
    ProjectMonthlyModel,
    ProjectMonthlyPageQueryModel,
)
from module_project_monthly.service.project_monthly_service import ProjectMonthlyService
from utils.log_util import logger
from utils.response_util import ResponseUtil

project_monthly_controller = APIRouterPro(
    prefix='/project/monthly',
    order_num=26,
    tags=['项目管理 - 月度项目台账'],
    dependencies=[PreAuthDependency()],
)


@project_monthly_controller.get(
    '/list',
    summary='获取月度项目台账分页列表',
    response_model=PageResponseModel[dict],
    dependencies=[UserInterfaceAuthDependency('project:monthly:list')],
)
async def get_project_monthly_list(
        request: Request,
        query_object: Annotated[ProjectMonthlyPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ProjectMonthlyService.get_project_monthly_list_services(query_db, query_object, is_page=True)
    return ResponseUtil.success(model_content=result)


@project_monthly_controller.get(
    '/detail/{id}',
    summary='获取月度项目台账详情',
    response_model=DataResponseModel[ProjectMonthlyModel],
    dependencies=[UserInterfaceAuthDependency('project:monthly:query')],
)
async def get_project_monthly_detail(
        request: Request,
        record_id: Annotated[int, Path(alias='id', description='记录ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ProjectMonthlyService.project_monthly_detail_services(query_db, record_id)
    return ResponseUtil.success(model_content=result)


@project_monthly_controller.post(
    '',
    summary='新增月度项目台账',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:monthly:add')],
)
@Log(title='月度项目台账', business_type=BusinessType.INSERT)
async def add_project_monthly(
        request: Request,
        add_model: AddProjectMonthlyModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user else 0
    result = await ProjectMonthlyService.add_project_monthly_services(query_db, add_model, user_id)
    return ResponseUtil.success(model_content=result)


@project_monthly_controller.put(
    '',
    summary='编辑月度项目台账',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:monthly:edit')],
)
@Log(title='月度项目台账', business_type=BusinessType.UPDATE)
async def edit_project_monthly(
        request: Request,
        edit_model: EditProjectMonthlyModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ProjectMonthlyService.edit_project_monthly_services(query_db, edit_model)
    return ResponseUtil.success(model_content=result)


@project_monthly_controller.delete(
    '/{id}',
    summary='删除月度项目台账',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:monthly:remove')],
)
@Log(title='月度项目台账', business_type=BusinessType.DELETE)
async def delete_project_monthly(
        request: Request,
        record_id: Annotated[int, Path(alias='id', description='记录ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ProjectMonthlyService.delete_project_monthly_services(
        query_db, DeleteProjectMonthlyModel(id=record_id)
    )
    return ResponseUtil.success(model_content=result)


@project_monthly_controller.get(
    '/template',
    summary='下载月度项目台账导入模板',
    dependencies=[UserInterfaceAuthDependency('project:monthly:import')],
)
async def download_project_monthly_template(request: Request) -> Response:
    try:
        template = ProjectMonthlyService.generate_import_template()
        filename = f'月度项目台账导入模板_{datetime.now().strftime("%Y%m%d")}.xlsx'
        encoded_filename = urllib.parse.quote(filename)
        response = StreamingResponse(
            template,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
        response.headers['Content-Encoding'] = 'identity'
        return response
    except ServiceException as exc:
        return ResponseUtil.error(msg=exc.message)
    except Exception as exc:
        logger.error(f'下载月度项目台账模板失败：{exc}', exc_info=True)
        return ResponseUtil.error(msg='下载模板失败')


@project_monthly_controller.post(
    '/import',
    summary='导入月度项目台账',
    response_model=ProjectMonthlyImportResponseModel,
    dependencies=[UserInterfaceAuthDependency('project:monthly:import')],
)
@Log(title='月度项目台账', business_type=BusinessType.IMPORT)
async def import_project_monthly(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        file: Annotated[UploadFile, File(description='Excel文件')],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    try:
        user_id = current_user.user.user_id if current_user.user else 0
        result = await ProjectMonthlyService.import_project_monthly_services(query_db, file, user_id)
        return ResponseUtil.success(model_content=result)
    except ServiceException as exc:
        return ResponseUtil.error(msg=exc.message)
    except Exception as exc:
        logger.error(f'导入月度项目台账失败：{exc}', exc_info=True)
        return ResponseUtil.error(msg='导入失败')


@project_monthly_controller.get(
    '/export',
    summary='导出月度项目台账',
    dependencies=[UserInterfaceAuthDependency('project:monthly:export')],
)
@Log(title='月度项目台账', business_type=BusinessType.EXPORT)
async def export_project_monthly(
        request: Request,
        query_object: Annotated[ProjectMonthlyPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ProjectMonthlyService.export_project_monthly_services(query_db, query_object)
    filename = f'月度项目台账_{query_object.stat_month or ProjectMonthlyService.default_stat_month()}.xlsx'
    encoded_filename = urllib.parse.quote(filename)
    return StreamingResponse(
        io.BytesIO(result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"},
    )
