from typing import Annotated

from fastapi import Path, Query, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.car_vo import (
    AddCarModel,
    DeleteCarModel,
    EditCarModel,
    CarPageQueryModel,
    CarRepairPageQueryModel,
    AddCarRepairModel,
    EditCarRepairModel,
    DeleteCarRepairModel,
    CarFeePageQueryModel,
    AddCarFeeModel,
    EditCarFeeModel,
    DeleteCarFeeModel,
    CarMileagePageQueryModel,
    AddCarMileageModel,
    EditCarMileageModel,
    DeleteCarMileageModel,
)
from module_admin.service.car_service import (
    CarService,
    CarRepairService,
    CarFeeService,
    CarMileageService,
)
from utils.log_util import logger
from utils.response_util import ResponseUtil

car_controller = APIRouterPro(
    prefix='/system/car', order_num=28, tags=['系统管理 - 车辆管理'], dependencies=[PreAuthDependency()]
)


# ==================== 车辆管理接口 ====================

@car_controller.get(
    '/list',
    summary='获取车辆分页列表接口',
    description='用于获取车辆分页列表',
    response_model=PageResponseModel[CarPageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:car:list')],
)
async def get_car_list(
        request: Request,
        car_page_query: Annotated[CarPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    car_page_query_result = await CarService.get_car_list_services(query_db, car_page_query, is_page=True)
    logger.info('获取车辆列表成功')

    return ResponseUtil.success(model_content=car_page_query_result)


@car_controller.post(
    '',
    summary='新增车辆接口',
    description='用于新增车辆',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:add')],
)
@ValidateFields(validate_model='add_car')
@Log(title='车辆管理', business_type=BusinessType.INSERT)
async def add_car(
        request: Request,
        add_car: AddCarModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_car_result = await CarService.add_car_services(request, query_db, add_car)
    logger.info(add_car_result.message)

    return ResponseUtil.success(msg=add_car_result.message)


@car_controller.put(
    '',
    summary='编辑车辆接口',
    description='用于编辑车辆',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:edit')],
)
@ValidateFields(validate_model='edit_car')
@Log(title='车辆管理', business_type=BusinessType.UPDATE)
async def edit_car(
        request: Request,
        edit_car: EditCarModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_car_result = await CarService.edit_car_services(request, query_db, edit_car)
    logger.info(edit_car_result.message)

    return ResponseUtil.success(msg=edit_car_result.message)


@car_controller.delete(
    '/{id}',
    summary='删除车辆接口',
    description='用于删除车辆',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:remove')],
)
@Log(title='车辆管理', business_type=BusinessType.DELETE)
async def delete_car(
        request: Request,
        id: Annotated[int, Path(description='需要删除的车辆 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_car = DeleteCarModel(id=id)
    delete_car_result = await CarService.delete_car_services(request, query_db, delete_car)
    logger.info(delete_car_result.message)

    return ResponseUtil.success(msg=delete_car_result.message)


@car_controller.get(
    '/{id}',
    summary='获取车辆详情接口',
    description='用于获取指定车辆的详细信息',
    response_model=DataResponseModel[CarPageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:car:query')],
)
async def query_car_detail(
        request: Request,
        id: Annotated[int, Path(description='车辆 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_car_result = await CarService.car_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的车辆信息成功')

    return ResponseUtil.success(data=detail_car_result)


# ==================== 维修/保养记录接口 ====================

@car_controller.get(
    '/repair/list',
    summary='获取维修/保养记录分页列表接口',
    description='用于获取维修/保养记录分页列表',
    response_model=PageResponseModel[CarRepairPageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:car:repair:list')],
)
async def get_car_repair_list(
        request: Request,
        car_repair_page_query: Annotated[CarRepairPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    repair_page_query_result = await CarRepairService.get_car_repair_list_services(
        query_db, car_repair_page_query, is_page=True
    )
    logger.info('获取维修/保养记录列表成功')

    return ResponseUtil.success(model_content=repair_page_query_result)


@car_controller.post(
    '/repair',
    summary='新增维修/保养记录接口',
    description='用于新增维修/保养记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:repair:add')],
)
@ValidateFields(validate_model='add_car_repair')
@Log(title='维修/保养记录', business_type=BusinessType.INSERT)
async def add_car_repair(
        request: Request,
        add_car_repair: AddCarRepairModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_car_repair_result = await CarRepairService.add_car_repair_services(request, query_db, add_car_repair)
    logger.info(add_car_repair_result.message)

    return ResponseUtil.success(msg=add_car_repair_result.message)


@car_controller.put(
    '/repair',
    summary='编辑维修/保养记录接口',
    description='用于编辑维修/保养记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:repair:edit')],
)
@ValidateFields(validate_model='edit_car_repair')
@Log(title='维修/保养记录', business_type=BusinessType.UPDATE)
async def edit_car_repair(
        request: Request,
        edit_car_repair: EditCarRepairModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_car_repair_result = await CarRepairService.edit_car_repair_services(request, query_db, edit_car_repair)
    logger.info(edit_car_repair_result.message)

    return ResponseUtil.success(msg=edit_car_repair_result.message)


@car_controller.delete(
    '/repair/{id}',
    summary='删除维修/保养记录接口',
    description='用于删除维修/保养记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:repair:remove')],
)
@Log(title='维修/保养记录', business_type=BusinessType.DELETE)
async def delete_car_repair(
        request: Request,
        id: Annotated[int, Path(description='需要删除的记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_car_repair = DeleteCarRepairModel(id=id)
    delete_car_repair_result = await CarRepairService.delete_car_repair_services(
        request, query_db, delete_car_repair
    )
    logger.info(delete_car_repair_result.message)

    return ResponseUtil.success(msg=delete_car_repair_result.message)


@car_controller.get(
    '/repair/{id}',
    summary='获取维修/保养记录详情接口',
    description='用于获取指定维修/保养记录的详细信息',
    response_model=DataResponseModel[CarRepairPageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:car:repair:query')],
)
async def query_car_repair_detail(
        request: Request,
        id: Annotated[int, Path(description='记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_car_repair_result = await CarRepairService.car_repair_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的维修/保养记录信息成功')

    return ResponseUtil.success(data=detail_car_repair_result)


# ==================== 费用记录接口 ====================

@car_controller.get(
    '/fee/list',
    summary='获取费用记录分页列表接口',
    description='用于获取费用记录分页列表',
    response_model=PageResponseModel[CarFeePageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:car:fee:list')],
)
async def get_car_fee_list(
        request: Request,
        car_fee_page_query: Annotated[CarFeePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    fee_page_query_result = await CarFeeService.get_car_fee_list_services(
        query_db, car_fee_page_query, is_page=True
    )
    logger.info('获取费用记录列表成功')

    return ResponseUtil.success(model_content=fee_page_query_result)


@car_controller.post(
    '/fee',
    summary='新增费用记录接口',
    description='用于新增费用记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:fee:add')],
)
@ValidateFields(validate_model='add_car_fee')
@Log(title='费用记录', business_type=BusinessType.INSERT)
async def add_car_fee(
        request: Request,
        add_car_fee: AddCarFeeModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_car_fee_result = await CarFeeService.add_car_fee_services(request, query_db, add_car_fee)
    logger.info(add_car_fee_result.message)

    return ResponseUtil.success(msg=add_car_fee_result.message)


@car_controller.put(
    '/fee',
    summary='编辑费用记录接口',
    description='用于编辑费用记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:fee:edit')],
)
@ValidateFields(validate_model='edit_car_fee')
@Log(title='费用记录', business_type=BusinessType.UPDATE)
async def edit_car_fee(
        request: Request,
        edit_car_fee: EditCarFeeModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_car_fee_result = await CarFeeService.edit_car_fee_services(request, query_db, edit_car_fee)
    logger.info(edit_car_fee_result.message)

    return ResponseUtil.success(msg=edit_car_fee_result.message)


@car_controller.delete(
    '/fee/{id}',
    summary='删除费用记录接口',
    description='用于删除费用记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:fee:remove')],
)
@Log(title='费用记录', business_type=BusinessType.DELETE)
async def delete_car_fee(
        request: Request,
        id: Annotated[int, Path(description='需要删除的费用记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_car_fee = DeleteCarFeeModel(id=id)
    delete_car_fee_result = await CarFeeService.delete_car_fee_services(
        request, query_db, delete_car_fee
    )
    logger.info(delete_car_fee_result.message)

    return ResponseUtil.success(msg=delete_car_fee_result.message)


@car_controller.get(
    '/fee/{id}',
    summary='获取费用记录详情接口',
    description='用于获取指定费用记录的详细信息',
    response_model=DataResponseModel[CarFeePageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:car:fee:query')],
)
async def query_car_fee_detail(
        request: Request,
        id: Annotated[int, Path(description='费用记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_car_fee_result = await CarFeeService.car_fee_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的费用记录信息成功')

    return ResponseUtil.success(data=detail_car_fee_result)


# ==================== 里程记录接口 ====================

@car_controller.get(
    '/mileage/list',
    summary='获取里程记录分页列表接口',
    description='用于获取里程记录分页列表',
    response_model=PageResponseModel[CarMileagePageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:car:mileage:list')],
)
async def get_car_mileage_list(
        request: Request,
        car_mileage_page_query: Annotated[CarMileagePageQueryModel, Query()],
        car_id: Annotated[int, Query(description='车辆 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    mileage_page_query_result = await CarMileageService.get_car_mileage_list_services(
        query_db, car_mileage_page_query, car_id, is_page=True
    )
    logger.info('获取里程记录列表成功')

    return ResponseUtil.success(model_content=mileage_page_query_result)


@car_controller.post(
    '/mileage',
    summary='新增里程记录接口',
    description='用于新增里程记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:mileage:add')],
)
@ValidateFields(validate_model='add_car_mileage')
@Log(title='里程记录', business_type=BusinessType.INSERT)
async def add_car_mileage(
        request: Request,
        add_car_mileage: AddCarMileageModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_car_mileage_result = await CarMileageService.add_car_mileage_services(request, query_db, add_car_mileage)
    logger.info(add_car_mileage_result.message)

    return ResponseUtil.success(msg=add_car_mileage_result.message)


@car_controller.put(
    '/mileage',
    summary='编辑里程记录接口',
    description='用于编辑里程记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:mileage:edit')],
)
@ValidateFields(validate_model='edit_car_mileage')
@Log(title='里程记录', business_type=BusinessType.UPDATE)
async def edit_car_mileage(
        request: Request,
        edit_car_mileage: EditCarMileageModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_car_mileage_result = await CarMileageService.edit_car_mileage_services(request, query_db, edit_car_mileage)
    logger.info(edit_car_mileage_result.message)

    return ResponseUtil.success(msg=edit_car_mileage_result.message)


@car_controller.delete(
    '/mileage/{id}',
    summary='删除里程记录接口',
    description='用于删除里程记录',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:mileage:remove')],
)
@Log(title='里程记录', business_type=BusinessType.DELETE)
async def delete_car_mileage(
        request: Request,
        id: Annotated[int, Path(description='需要删除的里程记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_car_mileage = DeleteCarMileageModel(id=id)
    delete_car_mileage_result = await CarMileageService.delete_car_mileage_services(
        request, query_db, delete_car_mileage
    )
    logger.info(delete_car_mileage_result.message)

    return ResponseUtil.success(msg=delete_car_mileage_result.message)


@car_controller.get(
    '/mileage/{id}',
    summary='获取里程记录详情接口',
    description='用于获取指定里程记录的详细信息',
    response_model=DataResponseModel[CarMileagePageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:car:mileage:query')],
)
async def query_car_mileage_detail(
        request: Request,
        id: Annotated[int, Path(description='里程记录 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_car_mileage_result = await CarMileageService.car_mileage_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的里程记录信息成功')

    return ResponseUtil.success(data=detail_car_mileage_result)


@car_controller.get(
    '/mileage/latest/{car_id}',
    summary='获取车辆最新里程接口',
    description='用于获取指定车辆的最新里程数',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('system:car:mileage:query')],
)
async def query_latest_mileage(
        request: Request,
        car_id: Annotated[int, Path(description='车辆 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    latest_mileage = await CarMileageService.get_latest_mileage_services(query_db, car_id)
    logger.info(f'获取车辆{car_id}的最新里程成功')

    return ResponseUtil.success(data={'latestMileage': latest_mileage})
