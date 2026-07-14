"""
投标文件知识库管理控制器
"""
from typing import Annotated

from fastapi import Path, Query, Request, Response, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_bid_kb.entity.vo.bid_vo import BidDocumentPageQueryModel
from module_bid_kb.service.bid_kb_service import BidKbService
from utils.file_util import allowed_resume_file, generate_resume_file_path, save_upload_file
from utils.log_util import logger
from utils.response_util import ResponseUtil

bid_kb_controller = APIRouterPro(
    prefix='/bid', order_num=41, tags=['投标文件知识库'], dependencies=[PreAuthDependency()]
)


@bid_kb_controller.post(
    '/upload',
    summary='上传投标文件并解析接口',
    description='上传投标文件PDF，自动识别人员列表、拆分简历并解析入库',
    dependencies=[UserInterfaceAuthDependency('bid-kb:add')],
)
@Log(title='投标文件知识库', business_type=BusinessType.INSERT)
async def upload_bid_document(
        request: Request,
        file: Annotated[UploadFile, File(description='投标文件')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    上传并解析投标文件
    """
    if not file or not file.filename:
        return ResponseUtil.failure(msg='上传文件不能为空')

    # 校验文件类型
    if not allowed_resume_file(file.filename):
        return ResponseUtil.failure(msg='仅支持 PDF 格式的投标文件')

    try:
        # 生成文件路径
        relative_path, absolute_path = generate_resume_file_path(file.filename)

        # 保存上传文件
        await save_upload_file(file, absolute_path)
        logger.info(f'投标文件已保存: {absolute_path}')

        # 解析投标文件
        result = await BidKbService.upload_bid_document_services(
            query_db, absolute_path, file.filename, current_user.user.user_id
        )

        return ResponseUtil.success(msg=result.message, model_content=result)

    except Exception as e:
        logger.error(f'上传投标文件失败: {str(e)}')
        return ResponseUtil.failure(msg=f'上传投标文件失败: {str(e)}')


@bid_kb_controller.get(
    '/list',
    summary='获取投标文件列表接口',
    description='获取投标文件列表，支持按项目名称、编号、公司筛选',
    dependencies=[UserInterfaceAuthDependency('bid-kb:list')],
)
async def get_bid_document_list(
        request: Request,
        query_object: Annotated[BidDocumentPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取投标文件列表
    """
    try:
        result = await BidKbService.get_bid_document_list_services(
            query_db, query_object, is_page=True
        )
        return ResponseUtil.success(model_content=result)
    except Exception as e:
        logger.error(f'查询投标文件列表失败: {str(e)}')
        return ResponseUtil.failure(msg=f'查询投标文件列表失败: {str(e)}')


@bid_kb_controller.get(
    '/detail/{bid_id}',
    summary='获取投标文件详情接口',
    description='获取投标文件详情，含关联简历列表',
    dependencies=[UserInterfaceAuthDependency('bid-kb:list')],
)
async def get_bid_detail(
        request: Request,
        bid_id: Annotated[int, Path(description='投标文件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取投标文件详情（含关联简历列表）
    """
    try:
        result = await BidKbService.get_bid_detail_services(query_db, bid_id)
        return ResponseUtil.success(data=result, msg='查询成功')
    except Exception as e:
        logger.error(f'查询投标文件详情失败: {str(e)}')
        return ResponseUtil.failure(msg=f'查询投标文件详情失败: {str(e)}')


@bid_kb_controller.delete(
    '/delete/{bid_id}',
    summary='删除投标文件接口',
    description='软删除投标文件及关联简历',
    dependencies=[UserInterfaceAuthDependency('bid-kb:delete')],
)
@Log(title='投标文件知识库', business_type=BusinessType.DELETE)
async def delete_bid_document(
        request: Request,
        bid_id: Annotated[int, Path(description='投标文件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    删除投标文件（软删除，关联简历一并标记删除）
    """
    try:
        result = await BidKbService.delete_bid_document_services(query_db, bid_id)
        return ResponseUtil.success(msg='删除成功')
    except Exception as e:
        logger.error(f'删除投标文件失败: {str(e)}')
        return ResponseUtil.failure(msg=f'删除投标文件失败: {str(e)}')


@bid_kb_controller.get(
    '/progress/{bid_uuid}',
    summary='查询投标文件解析进度',
    description='轮询获取投标文件OCR和LLM解析的实时进度',
    dependencies=[UserInterfaceAuthDependency('bid-kb:list')],
)
async def get_bid_progress(
        request: Request,
        bid_uuid: Annotated[str, Path(description='投标文件UUID')],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取投标文件解析进度
    """
    try:
        result = await BidKbService.get_bid_progress_services(bid_uuid)
        return ResponseUtil.success(data=result, msg='查询成功')
    except Exception as e:
        logger.error(f'查询解析进度失败: {str(e)}')
        return ResponseUtil.failure(msg=f'查询解析进度失败: {str(e)}')
