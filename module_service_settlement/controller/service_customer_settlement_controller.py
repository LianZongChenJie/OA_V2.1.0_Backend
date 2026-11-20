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
from module_service_settlement.entity.vo.service_customer_settlement_vo import (
    AddServiceCustomerSettlementModel,
    DeleteServiceCustomerSettlementModel,
    EditServiceCustomerSettlementModel,
    ServiceCustomerSettlementImportResponseModel,
    ServiceCustomerSettlementModel,
    ServiceCustomerSettlementPageQueryModel,
)
from module_service_settlement.service.service_customer_settlement_service import ServiceCustomerSettlementService
from utils.log_util import logger
from utils.response_util import ResponseUtil

service_customer_settlement_controller = APIRouterPro(
    prefix='/service/customer/settlement',
    order_num=27,
    tags=['服务客户结算'],
    dependencies=[PreAuthDependency()],
)


@service_customer_settlement_controller.get(
    '/list',
    summary='获取服务客户结算分页列表',
    response_model=PageResponseModel[dict],
    dependencies=[UserInterfaceAuthDependency('service:customerSettlement:list')],
)
async def get_service_customer_settlement_list(
        request: Request,
        query_object: Annotated[ServiceCustomerSettlementPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ServiceCustomerSettlementService.get_service_customer_settlement_list_services(
        query_db, query_object, is_page=True
    )
    return ResponseUtil.success(model_content=result)


@service_customer_settlement_controller.get(
    '/detail/{id}',
    summary='获取服务客户结算详情',
    response_model=DataResponseModel[ServiceCustomerSettlementModel],
    dependencies=[UserInterfaceAuthDependency('service:customerSettlement:query')],
)
async def get_service_customer_settlement_detail(
        request: Request,
        record_id: Annotated[int, Path(alias='id', description='记录ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ServiceCustomerSettlementService.service_customer_settlement_detail_services(query_db, record_id)
    return ResponseUtil.success(model_content=result)


@service_customer_settlement_controller.post(
    '',
    summary='新增服务客户结算',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('service:customerSettlement:add')],
)
@Log(title='服务客户结算', business_type=BusinessType.INSERT)
async def add_service_customer_settlement(
        request: Request,
        add_model: AddServiceCustomerSettlementModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    user_id = current_user.user.user_id if current_user.user else 0
    result = await ServiceCustomerSettlementService.add_service_customer_settlement_services(
        query_db, add_model, user_id
    )
    return ResponseUtil.success(model_content=result)


@service_customer_settlement_controller.put(
    '',
    summary='编辑服务客户结算',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('service:customerSettlement:edit')],
)
@Log(title='服务客户结算', business_type=BusinessType.UPDATE)
async def edit_service_customer_settlement(
        request: Request,
        edit_model: EditServiceCustomerSettlementModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ServiceCustomerSettlementService.edit_service_customer_settlement_services(query_db, edit_model)
    return ResponseUtil.success(model_content=result)


@service_customer_settlement_controller.delete(
    '/{id}',
    summary='删除服务客户结算',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('service:customerSettlement:remove')],
)
@Log(title='服务客户结算', business_type=BusinessType.DELETE)
async def delete_service_customer_settlement(
        request: Request,
        record_id: Annotated[int, Path(alias='id', description='记录ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ServiceCustomerSettlementService.delete_service_customer_settlement_services(
        query_db, DeleteServiceCustomerSettlementModel(id=record_id)
    )
    return ResponseUtil.success(model_content=result)


@service_customer_settlement_controller.get(
    '/template',
    summary='下载服务客户结算导入模板',
    dependencies=[UserInterfaceAuthDependency('service:customerSettlement:import')],
)
async def download_service_customer_settlement_template(request: Request) -> Response:
    try:
        template = ServiceCustomerSettlementService.generate_import_template()
        filename = f'服务客户结算导入模板_{datetime.now().strftime("%Y%m%d")}.xlsx'
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
        logger.error(f'下载服务客户结算模板失败：{exc}', exc_info=True)
        return ResponseUtil.error(msg='下载模板失败')


@service_customer_settlement_controller.post(
    '/import',
    summary='导入服务客户结算',
    response_model=ServiceCustomerSettlementImportResponseModel,
    dependencies=[UserInterfaceAuthDependency('service:customerSettlement:import')],
)
@Log(title='服务客户结算', business_type=BusinessType.IMPORT)
async def import_service_customer_settlement(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        file: Annotated[UploadFile, File(description='Excel文件')],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    try:
        user_id = current_user.user.user_id if current_user.user else 0
        result = await ServiceCustomerSettlementService.import_service_customer_settlement_services(
            query_db, file, user_id
        )
        return ResponseUtil.success(model_content=result)
    except ServiceException as exc:
        return ResponseUtil.error(msg=exc.message)
    except Exception as exc:
        logger.error(f'导入服务客户结算失败：{exc}', exc_info=True)
        return ResponseUtil.error(msg='导入失败')


@service_customer_settlement_controller.get(
    '/export',
    summary='导出服务客户结算',
    dependencies=[UserInterfaceAuthDependency('service:customerSettlement:export')],
)
@Log(title='服务客户结算', business_type=BusinessType.EXPORT)
async def export_service_customer_settlement(
        request: Request,
        query_object: Annotated[ServiceCustomerSettlementPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ServiceCustomerSettlementService.export_service_customer_settlement_services(
        query_db, query_object
    )
    stat_year = query_object.stat_year or ServiceCustomerSettlementService.default_stat_year()
    month_part = f'-{int(query_object.stat_month):02d}' if query_object.stat_month else ''
    filename = f'服务客户结算_{stat_year}{month_part}.xlsx'
    encoded_filename = urllib.parse.quote(filename)
    return StreamingResponse(
        io.BytesIO(result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"},
    )
