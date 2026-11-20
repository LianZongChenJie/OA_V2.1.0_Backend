import io
import urllib.parse
from datetime import datetime
from typing import Annotated, Any

from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import CrudResponseModel, DataResponseModel, PageModel, PageResponseModel, ResponseBaseModel
from exceptions.exception import ServiceException
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_hr_cost.entity.vo.hr_cost_vo import (
    AddHrCostModel,
    EditHrCostModel,
    HrCostImportResponseModel,
    HrCostModel,
    HrCostPageQueryModel,
)
from module_hr_cost.service.hr_cost_service import HrCostService
from utils.log_util import logger
from utils.response_util import ResponseUtil

hr_cost_controller = APIRouterPro(
    prefix='/hr/cost',
    order_num=28,
    tags=['人力总成本'],
    dependencies=[PreAuthDependency()],
)


@hr_cost_controller.get(
    '/list',
    summary='获取人力总成本分页列表',
    response_model=PageResponseModel[dict],
    dependencies=[UserInterfaceAuthDependency('hr:cost:list')],
)
async def get_hr_cost_list(
        request: Request,
        query_object: Annotated[HrCostPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await HrCostService.get_hr_cost_list_services(query_db, query_object, is_page=True)
    return ResponseUtil.success(model_content=result)


@hr_cost_controller.get(
    '/detail/{id}',
    summary='获取人力总成本详情',
    response_model=DataResponseModel[HrCostModel],
    dependencies=[UserInterfaceAuthDependency('hr:cost:query')],
)
async def get_hr_cost_detail(
        request: Request,
        record_id: Annotated[int, Path(alias='id', description='记录ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await HrCostService.hr_cost_detail_services(query_db, record_id)
    return ResponseUtil.success(model_content=result)


@hr_cost_controller.post(
    '',
    summary='新增人力总成本',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('hr:cost:add')],
)
@Log(title='人力总成本', business_type=BusinessType.INSERT)
async def add_hr_cost(
        request: Request,
        add_model: AddHrCostModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user else 0
    result: CrudResponseModel = await HrCostService.add_hr_cost_services(query_db, add_model, user_id)
    return ResponseUtil.success(model_content=result)


@hr_cost_controller.put(
    '',
    summary='编辑人力总成本',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('hr:cost:edit')],
)
@Log(title='人力总成本', business_type=BusinessType.UPDATE)
async def edit_hr_cost(
        request: Request,
        edit_model: EditHrCostModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result: CrudResponseModel = await HrCostService.edit_hr_cost_services(query_db, edit_model)
    return ResponseUtil.success(model_content=result)


@hr_cost_controller.delete(
    '/{id}',
    summary='删除人力总成本',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('hr:cost:remove')],
)
@Log(title='人力总成本', business_type=BusinessType.DELETE)
async def delete_hr_cost(
        request: Request,
        record_id: Annotated[int, Path(alias='id', description='记录ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result: CrudResponseModel = await HrCostService.delete_hr_cost_services(query_db, record_id)
    return ResponseUtil.success(model_content=result)


@hr_cost_controller.get(
    '/template',
    summary='下载人力总成本导入模板',
    dependencies=[UserInterfaceAuthDependency('hr:cost:import')],
)
async def download_hr_cost_template(request: Request) -> Response:
    try:
        template = HrCostService.generate_import_template()
        filename = f'人力总成本导入模板_{datetime.now().strftime("%Y%m%d")}.xlsx'
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
        logger.error(f'下载人力成本模板失败：{exc}', exc_info=True)
        return ResponseUtil.error(msg='下载模板失败')


@hr_cost_controller.post(
    '/import',
    summary='导入人力总成本',
    response_model=HrCostImportResponseModel,
    dependencies=[UserInterfaceAuthDependency('hr:cost:import')],
)
@Log(title='人力总成本', business_type=BusinessType.IMPORT)
async def import_hr_cost(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        file: Annotated[UploadFile, File(description='Excel文件')],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
        stat_month: Annotated[str | None, Form(alias='statMonth', description='导入月份')] = None,
) -> Response:
    try:
        user_id = current_user.user.user_id if current_user.user else 0
        result = await HrCostService.import_hr_cost_services(query_db, file, user_id, stat_month)
        return ResponseUtil.success(model_content=result)
    except ServiceException as exc:
        return ResponseUtil.error(msg=exc.message)
    except Exception as exc:
        logger.error(f'导入人力成本失败：{exc}', exc_info=True)
        return ResponseUtil.error(msg='导入失败')


@hr_cost_controller.get(
    '/summary/org',
    summary='按组织架构汇总人力总成本',
    response_model=PageResponseModel[dict],
    dependencies=[UserInterfaceAuthDependency('hr:cost:list')],
)
async def get_hr_cost_org_summary(
        request: Request,
        query_object: Annotated[HrCostPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    rows = await HrCostService.get_summary_services(query_db, query_object, 'org')
    return ResponseUtil.success(model_content=PageModel[dict](rows=rows, pageNum=1, pageSize=len(rows) or 1, total=len(rows), hasNext=False))


@hr_cost_controller.get(
    '/summary/city',
    summary='按城市汇总人力总成本',
    response_model=PageResponseModel[dict],
    dependencies=[UserInterfaceAuthDependency('hr:cost:list')],
)
async def get_hr_cost_city_summary(
        request: Request,
        query_object: Annotated[HrCostPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    rows = await HrCostService.get_summary_services(query_db, query_object, 'city')
    return ResponseUtil.success(model_content=PageModel[dict](rows=rows, pageNum=1, pageSize=len(rows) or 1, total=len(rows), hasNext=False))


@hr_cost_controller.get(
    '/summary/org/export',
    summary='导出按组织架构汇总',
    dependencies=[UserInterfaceAuthDependency('hr:cost:export')],
)
@Log(title='人力总成本', business_type=BusinessType.EXPORT)
async def export_hr_cost_org_summary(
        request: Request,
        query_object: Annotated[HrCostPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await HrCostService.export_summary_services(query_db, query_object, 'org')
    month = query_object.stat_month or datetime.now().strftime('%Y-%m')
    filename = f'人力总成本_按架构_{month}.xlsx'
    encoded_filename = urllib.parse.quote(filename)
    return StreamingResponse(
        io.BytesIO(result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@hr_cost_controller.get(
    '/summary/city/export',
    summary='导出按城市汇总',
    dependencies=[UserInterfaceAuthDependency('hr:cost:export')],
)
@Log(title='人力总成本', business_type=BusinessType.EXPORT)
async def export_hr_cost_city_summary(
        request: Request,
        query_object: Annotated[HrCostPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await HrCostService.export_summary_services(query_db, query_object, 'city')
    month = query_object.stat_month or datetime.now().strftime('%Y-%m')
    filename = f'人力总成本_按城市_{month}.xlsx'
    encoded_filename = urllib.parse.quote(filename)
    return StreamingResponse(
        io.BytesIO(result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@hr_cost_controller.get(
    '/filter/options',
    summary='获取组织架构树与城市级联选项',
    response_model=DataResponseModel[dict[str, Any]],
    dependencies=[UserInterfaceAuthDependency('hr:cost:list')],
)
async def get_hr_cost_filter_options(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await HrCostService.get_filter_options_services(query_db)
    return ResponseUtil.success(data=result)


@hr_cost_controller.get(
    '/export',
    summary='按当前筛选条件导出人力总成本',
    dependencies=[UserInterfaceAuthDependency('hr:cost:export')],
)
@Log(title='人力总成本', business_type=BusinessType.EXPORT)
async def export_hr_cost(
        request: Request,
        query_object: Annotated[HrCostPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await HrCostService.export_hr_cost_services(query_db, query_object)
    month = query_object.stat_month or datetime.now().strftime('%Y-%m')
    filename = f'人力总成本_{month}.xlsx'
    encoded_filename = urllib.parse.quote(filename)
    return StreamingResponse(
        io.BytesIO(result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"},
    )
