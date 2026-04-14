from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel
from utils.log_util import logger
from utils.response_util import ResponseUtil
from utils.system_util import get_system_info

system_controller = APIRouterPro(
    prefix='/system', order_num=1, tags=['系统管理 - 系统信息'], dependencies=[PreAuthDependency()]
)


@system_controller.get(
    '/info',
    summary='获取系统信息接口',
    description='用于获取服务器系统信息，包括操作系统、Python版本、上传限制等',
    response_model=DataResponseModel[dict],
)
async def get_system_information(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取系统信息

    返回以下信息：
    - 服务器系统：操作系统类型
    - Python版本：当前运行的Python版本
    - 上传附件限制：单个文件/总上传大小限制
    - 执行时间限制：最大执行时间
    - 框架版本：Web框架及版本
    - Layui版本：前端UI框架版本
    """
    system_info = get_system_info()
    logger.info('获取系统信息成功')

    return ResponseUtil.success(data=system_info)
