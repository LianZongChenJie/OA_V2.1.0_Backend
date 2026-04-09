from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from module_basicdata.entity.vo.public.area_vo import AreaTreeModel, AreaBaseModel
from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated
from common.annotation.log_annotation import Log

from module_basicdata.service.public.area_service import AreaService
from utils.log_util import logger
from utils.response_util import ResponseUtil

area_controller = APIRouterPro(
    prefix='/basicdata/public/area', order_num=3, tags=['基础数据-公共模块-全国省市'], dependencies=[PreAuthDependency()]
)
@area_controller.get(
    "/tree",
    summary='获取审全国省市树形结构接口',
    description='获取审全国省市树形结构接口',
    response_model=list[AreaTreeModel],
    dependencies=[UserInterfaceAuthDependency('basicdata:area:tree')],
)
async def get_area_tree(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    area_model: Annotated[AreaBaseModel, Query()],
) -> Response:
    area_list = await AreaService.get_list_tree(query_db,area_model)
    return ResponseUtil.success(data=area_list)

@area_controller.post(
    "/add",
    summary='新增区域信息',
    description='新增区域信息',
    response_model=AreaTreeModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:area:add')],
)
@Log(title='区域信息', business_type=BusinessType.INSERT)
async def add_area(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    add_model: AreaBaseModel
) -> Response:
    area = await AreaService.save(query_db,add_model )
    return ResponseUtil.success(data=area.message)

@area_controller.put(
    "/update",
    summary='更新区域信息',
    description='更新区域信息',
    response_model=AreaTreeModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:area:update')],
)
@Log(title='区域信息', business_type=BusinessType.UPDATE)
async def update_area(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    update_model: AreaBaseModel
) -> Response:
    try:
        area = await AreaService.update(query_db,update_model)
        return ResponseUtil.success(data=area.message)
    except Exception as e:
        logger.error(e)
        return ResponseUtil.error(msg=e.message)

@area_controller.put(
    "/changeStatus",
    summary='修改状态',
    description='修改状态',
    response_model=AreaTreeModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:area:changeStatus')],
)
@Log(title='区域信息', business_type=BusinessType.UPDATE)
async def change_status(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    change_model: AreaBaseModel
) -> Response:
    try:
        area = await AreaService.change_status_area_service(query_db,change_model )
        return ResponseUtil.success(data=area.message)
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("更新失败")

@area_controller.get(
    "/getDataByLevel/{level}",
    summary='根据级别获取区域信息',
    description='根据级别获取区域信息',
    response_model=AreaTreeModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:area:getDataByLevel')],
)
@Log(title='区域信息', business_type=BusinessType.OTHER)
async def get_area_by_level(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    level: int = 1
) -> Response:
    try:
        area_list = await AreaService.get_area_by_level(query_db, level)
        return ResponseUtil.success(data=area_list)
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")


@area_controller.get(
    "/detail/{area_id}",
    summary='根据ID获取区域信息',
    description='根据ID获取区域信息',
    response_model=AreaBaseModel,
    dependencies=[UserInterfaceAuthDependency('basicdata:area:getById')],
)
@Log(title='区域信息', business_type=BusinessType.OTHER)
async def get_area_by_id(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    area_id: int
) -> Response:
    try:
        area = await AreaService.get_area_by_id(query_db, area_id)
        return ResponseUtil.success(data=area)
    except Exception as e:
        logger.error(e)
        return ResponseUtil.failure("查询失败")



