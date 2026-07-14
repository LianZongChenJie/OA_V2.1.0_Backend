"""
招标文件智能生成管理控制器
"""
import os
from typing import Annotated

from fastapi import Path, Query, Request, Response, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_tender.entity.vo.tender_vo import (
    TenderDocumentPageQueryModel,
    SelectPersonnelModel,
    GenerateBidFileModel,
)
from module_tender.service.tender_service import TenderService
from utils.file_util import allowed_resume_file, generate_resume_file_path, save_upload_file
from utils.log_util import logger
from utils.response_util import ResponseUtil

tender_controller = APIRouterPro(
    prefix='/tender', order_num=42, tags=['招标文件智能生成'], dependencies=[PreAuthDependency()]
)


@tender_controller.post(
    '/upload',
    summary='上传招标文件并解析接口',
    description='上传招标文件（PDF/Word），自动提取人员配置要求和评标标准',
    dependencies=[UserInterfaceAuthDependency('tender:add')],
)
@Log(title='招标文件智能生成', business_type=BusinessType.INSERT)
async def upload_tender_document(
        request: Request,
        file: Annotated[UploadFile, File(description='招标文件')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    上传并解析招标文件
    """
    if not file or not file.filename:
        return ResponseUtil.failure(msg='上传文件不能为空')

    # 校验文件类型
    if not allowed_resume_file(file.filename):
        return ResponseUtil.failure(msg='仅支持 PDF/Word/TXT 格式的招标文件')

    try:
        # 生成文件路径
        relative_path, absolute_path = generate_resume_file_path(file.filename)

        # 保存上传文件
        await save_upload_file(file, absolute_path)
        logger.info(f'招标文件已保存: {absolute_path}')

        # 解析招标文件
        result = await TenderService.upload_tender_document_services(
            query_db, absolute_path, file.filename, current_user.user.user_id
        )

        return ResponseUtil.success(msg=result.message, model_content=result)

    except Exception as e:
        logger.error(f'上传招标文件失败: {str(e)}')
        return ResponseUtil.failure(msg=f'上传招标文件失败: {str(e)}')


@tender_controller.get(
    '/list',
    summary='获取招标文件列表接口',
    description='获取招标文件列表，支持按项目名称、编号、招标单位筛选',
    dependencies=[UserInterfaceAuthDependency('tender:list')],
)
async def get_tender_document_list(
        request: Request,
        query_object: Annotated[TenderDocumentPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取招标文件列表
    """
    try:
        result = await TenderService.get_tender_document_list_services(
            query_db, query_object, is_page=True
        )
        return ResponseUtil.success(model_content=result)
    except Exception as e:
        logger.error(f'查询招标文件列表失败: {str(e)}')
        return ResponseUtil.failure(msg=f'查询招标文件列表失败: {str(e)}')


@tender_controller.get(
    '/detail/{tender_id}',
    summary='获取招标文件详情接口',
    description='获取招标文件详情，含人员配置要求列表',
    dependencies=[UserInterfaceAuthDependency('tender:list')],
)
async def get_tender_detail(
        request: Request,
        tender_id: Annotated[int, Path(description='招标文件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取招标文件详情（含人员配置要求列表）
    """
    try:
        result = await TenderService.get_tender_detail_services(query_db, tender_id)
        return ResponseUtil.success(data=result, msg='查询成功')
    except Exception as e:
        logger.error(f'查询招标文件详情失败: {str(e)}')
        return ResponseUtil.failure(msg=f'查询招标文件详情失败: {str(e)}')


@tender_controller.get(
    '/requirements/{tender_id}',
    summary='获取结构化招标要求接口',
    description='获取招标文件的结构化人员要求列表',
    dependencies=[UserInterfaceAuthDependency('tender:list')],
)
async def get_tender_requirements(
        request: Request,
        tender_id: Annotated[int, Path(description='招标文件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取招标文件的结构化要求列表
    """
    try:
        result = await TenderService.get_tender_requirements_services(query_db, tender_id)
        return ResponseUtil.success(data=result, msg='查询成功')
    except Exception as e:
        logger.error(f'查询招标要求失败: {str(e)}')
        return ResponseUtil.failure(msg=f'查询招标要求失败: {str(e)}')


@tender_controller.post(
    '/match/{tender_id}',
    summary='执行人员匹配推荐接口',
    description='根据招标文件要求，从简历知识库中匹配推荐人员',
    dependencies=[UserInterfaceAuthDependency('tender:match')],
)
@Log(title='招标文件智能生成', business_type=BusinessType.OTHER)
async def match_personnel(
        request: Request,
        tender_id: Annotated[int, Path(description='招标文件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    执行人员匹配推荐
    """
    try:
        result = await TenderService.match_personnel_services(query_db, tender_id)
        return ResponseUtil.success(data=result, msg='匹配完成')
    except Exception as e:
        logger.error(f'人员匹配失败: {str(e)}')
        return ResponseUtil.failure(msg=f'人员匹配失败: {str(e)}')


@tender_controller.get(
    '/match-result/{tender_id}',
    summary='获取匹配结果列表接口',
    description='获取招标文件的人员匹配推荐结果',
    dependencies=[UserInterfaceAuthDependency('tender:list')],
)
async def get_match_result(
        request: Request,
        tender_id: Annotated[int, Path(description='招标文件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取匹配结果列表
    """
    try:
        result = await TenderService.get_match_result_services(query_db, tender_id)
        return ResponseUtil.success(data=result, msg='查询成功')
    except Exception as e:
        logger.error(f'查询匹配结果失败: {str(e)}')
        return ResponseUtil.failure(msg=f'查询匹配结果失败: {str(e)}')


@tender_controller.post(
    '/select-personnel',
    summary='选择/取消选择人员接口',
    description='选择或取消选择匹配推荐的人员',
    dependencies=[UserInterfaceAuthDependency('tender:select')],
)
@Log(title='招标文件智能生成', business_type=BusinessType.UPDATE)
async def select_personnel(
        request: Request,
        select_model: SelectPersonnelModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    选择/取消选择人员
    """
    try:
        result = await TenderService.select_personnel_services(
            query_db, select_model.mapping_id, select_model.is_selected
        )
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'选择人员失败: {str(e)}')
        return ResponseUtil.failure(msg=f'选择人员失败: {str(e)}')


@tender_controller.post(
    '/generate',
    summary='生成投标文件接口',
    description='根据选中人员自动生成标准格式投标文件（Word）',
    dependencies=[UserInterfaceAuthDependency('tender:generate')],
)
@Log(title='招标文件智能生成', business_type=BusinessType.EXPORT)
async def generate_bid_file(
        request: Request,
        generate_model: GenerateBidFileModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    生成投标文件
    """
    try:
        file_path = await TenderService.generate_bid_file_services(
            query_db, generate_model.tender_id, generate_model.output_format
        )
        file_name = os.path.basename(file_path)
        return ResponseUtil.success(
            data={'file_path': file_path, 'file_name': file_name},
            msg='投标文件生成成功'
        )
    except Exception as e:
        logger.error(f'生成投标文件失败: {str(e)}')
        return ResponseUtil.failure(msg=f'生成投标文件失败: {str(e)}')


@tender_controller.get(
    '/download/{tender_id}',
    summary='下载生成的投标文件接口',
    description='下载已生成的投标文件',
    dependencies=[UserInterfaceAuthDependency('tender:list')],
)
async def download_bid_file(
        request: Request,
        tender_id: Annotated[int, Path(description='招标文件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    下载生成的投标文件
    """
    try:
        file_path = await TenderService.download_bid_file_services(query_db, tender_id)
        file_name = os.path.basename(file_path)
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        logger.error(f'下载投标文件失败: {str(e)}')
        return ResponseUtil.failure(msg=f'下载投标文件失败: {str(e)}')


@tender_controller.delete(
    '/delete/{tender_id}',
    summary='删除招标文件接口',
    description='删除招标文件及关联数据',
    dependencies=[UserInterfaceAuthDependency('tender:delete')],
)
@Log(title='招标文件智能生成', business_type=BusinessType.DELETE)
async def delete_tender_document(
        request: Request,
        tender_id: Annotated[int, Path(description='招标文件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    删除招标文件
    """
    try:
        result = await TenderService.delete_tender_document_services(query_db, tender_id)
        return ResponseUtil.success(msg='删除成功')
    except Exception as e:
        logger.error(f'删除招标文件失败: {str(e)}')
        return ResponseUtil.failure(msg=f'删除招标文件失败: {str(e)}')
