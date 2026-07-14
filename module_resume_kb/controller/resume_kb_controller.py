"""
简历知识库管理控制器
"""
from typing import Annotated

from fastapi import Path, Query, Request, Response, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_resume_kb.entity.vo.resume_vo import (
    ResumeModel,
    ResumePageQueryModel,
    ResumeUploadResultModel,
    ResumeSearchResultModel,
    ResumeChatRequestModel,
)
from module_resume_kb.service.resume_kb_service import ResumeKbService
from utils.file_util import allowed_resume_file, generate_resume_file_path, save_upload_file
from utils.log_util import logger
from utils.response_util import ResponseUtil

resume_kb_controller = APIRouterPro(
    prefix='/resume-kb', order_num=40, tags=['简历知识库模块'], dependencies=[PreAuthDependency()]
)


@resume_kb_controller.post(
    '/upload',
    summary='上传简历并解析入库接口',
    description='上传简历文件（PDF/Word/图片等），自动解析提取结构化信息并入库',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume-kb:add')],
)
@Log(title='简历知识库管理', business_type=BusinessType.INSERT)
async def upload_resume(
        request: Request,
        file: Annotated[UploadFile, File(description='简历文件')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    上传简历并解析入库
    """
    # 检查文件是否为空
    if not file or not file.filename:
        return ResponseUtil.failure(msg='上传文件不能为空')

    # 检查文件类型
    if not allowed_resume_file(file.filename):
        return ResponseUtil.failure(
            msg=f'不支持的文件类型，支持: pdf, docx, doc, txt, png, jpg, jpeg'
        )

    try:
        # 生成文件路径
        relative_path, absolute_path = generate_resume_file_path(file.filename)

        # 保存文件
        await save_upload_file(file, absolute_path)
        logger.info(f'简历文件已保存: {absolute_path}')

        # 解析入库
        upload_result = await ResumeKbService.upload_resume_services(
            request, query_db, absolute_path, file.filename, current_user.user.user_id
        )

        if upload_result.success:
            return ResponseUtil.success(
                msg='简历解析入库成功',
                model_content=upload_result,
            )
        else:
            return ResponseUtil.failure(msg=upload_result.message)

    except Exception as e:
        logger.error(f'简历上传失败: {str(e)}')
        return ResponseUtil.failure(msg=f'简历上传失败: {str(e)}')


@resume_kb_controller.get(
    '/list',
    summary='获取简历列表接口',
    description='用于获取简历列表，支持按学历、年龄、技能、专业、关键词等条件筛选',
    response_model=PageResponseModel[ResumeModel],
    dependencies=[UserInterfaceAuthDependency('resume-kb:list')],
)
async def get_resume_list(
        request: Request,
        resume_page_query: Annotated[ResumePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取简历列表
    """
    where_conditions = await ResumeKbService.build_query_conditions(
        resume_page_query, current_user.user.user_id
    )

    resume_list_result = await ResumeKbService.get_resume_list_services(
        query_db, resume_page_query, current_user.user.user_id, where_conditions, is_page=True
    )
    logger.info('获取简历列表成功')

    return ResponseUtil.success(model_content=resume_list_result)


@resume_kb_controller.get(
    '/search',
    summary='简历检索接口',
    description='按条件检索简历，支持学历、年龄范围、技能、专业、全文关键词等条件',
    response_model=ResumeSearchResultModel,
    dependencies=[UserInterfaceAuthDependency('resume-kb:list')],
)
async def search_resumes(
        request: Request,
        name: Annotated[str | None, Query(description='姓名关键词')] = None,
        education: Annotated[str | None, Query(description='学历筛选')] = None,
        min_age: Annotated[int | None, Query(description='最小年龄')] = None,
        max_age: Annotated[int | None, Query(description='最大年龄')] = None,
        skill: Annotated[str | None, Query(description='技能关键词')] = None,
        major: Annotated[str | None, Query(description='专业关键词')] = None,
        company: Annotated[str | None, Query(description='公司关键词')] = None,
        position: Annotated[str | None, Query(description='职位关键词')] = None,
        project_keyword: Annotated[str | None, Query(description='项目经验关键词')] = None,
        keyword: Annotated[str | None, Query(description='全文关键词')] = None,
        page_num: Annotated[int, Query(description='当前页码')] = 1,
        page_size: Annotated[int, Query(description='每页记录数')] = 10,
        query_db: Annotated[AsyncSession, DBSessionDependency()] = None,
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()] = None,
) -> Response:
    """
    简历检索
    """
    try:
        resume_page_query = ResumePageQueryModel(
            page_num=page_num,
            page_size=page_size,
            name=name,
            education=education,
            min_age=min_age,
            max_age=max_age,
            skill=skill,
            major=major,
            company=company,
            position=position,
            project_keyword=project_keyword,
            keyword=keyword,
        )

        where_conditions = await ResumeKbService.build_query_conditions(
            resume_page_query, current_user.user.user_id
        )

        resume_list_result = await ResumeKbService.get_resume_list_services(
            query_db, resume_page_query, current_user.user.user_id, where_conditions, is_page=True
        )

        # 构建搜索结果
        total = getattr(resume_list_result, 'total', 0) if hasattr(resume_list_result, 'total') else 0
        rows = getattr(resume_list_result, 'rows', []) if hasattr(resume_list_result, 'rows') else resume_list_result

        # 处理脱敏
        processed_rows = []
        for row in rows:
            if isinstance(row, dict):
                processed_rows.append(row)
            elif hasattr(row, '__dict__'):
                row_dict = row.__dict__.copy()
                # 联系方式脱敏
                if row_dict.get('phone'):
                    phone = row_dict['phone']
                    row_dict['phone'] = phone[:3] + '****' + phone[-4:] if len(phone) >= 7 else phone
                if row_dict.get('email'):
                    email = row_dict['email']
                    if '@' in email and len(email) > 5:
                        at_idx = email.index('@')
                        row_dict['email'] = email[:2] + '***' + email[at_idx:] if at_idx > 2 else email
                processed_rows.append(row_dict)

        result = {
            'total': total,
            'resumes': processed_rows,
        }

        return ResponseUtil.success(data=result, msg='查询成功')

    except Exception as e:
        logger.error(f'简历检索失败: {str(e)}')
        return ResponseUtil.failure(msg=f'简历检索失败: {str(e)}')


@resume_kb_controller.get(
    '/{id}',
    summary='获取简历详情接口',
    description='用于获取指定简历的详细信息（含工作经历和项目经验）',
    response_model=DataResponseModel[ResumeModel],
    dependencies=[UserInterfaceAuthDependency('resume-kb:query')],
)
async def query_resume_detail(
        request: Request,
        id: Annotated[int, Path(description='简历 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取简历详情
    """
    detail_result = await ResumeKbService.get_resume_detail_services(query_db, id)

    if not detail_result or not detail_result.id:
        return ResponseUtil.failure(msg='简历不存在')

    logger.info(f'获取 id 为{id}的简历详情成功')
    return ResponseUtil.success(data=detail_result)


@resume_kb_controller.delete(
    '/{id}',
    summary='删除简历接口',
    description='删除简历（逻辑删除）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume-kb:remove')],
)
@Log(title='简历知识库管理', business_type=BusinessType.DELETE)
async def delete_resume(
        request: Request,
        id: Annotated[int, Path(description='简历 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    删除简历
    """
    try:
        delete_result = await ResumeKbService.delete_resume_services(
            query_db, id, current_user.user.user_id
        )
        logger.info(delete_result.message)
        return ResponseUtil.success(msg=delete_result.message)
    except Exception as e:
        logger.error(f'删除简历失败: {str(e)}')
        return ResponseUtil.failure(msg=f'删除简历失败: {str(e)}')


@resume_kb_controller.post(
    '/chat',
    summary='简历智能问答接口',
    description='基于简历库的RAG智能问答，自动检索相关简历并生成回答',
    response_class=StreamingResponse,
    responses={
        200: {
            'description': '流式返回问答结果',
            'content': {
                'text/event-stream': {},
            },
        }
    },
    dependencies=[UserInterfaceAuthDependency('resume-kb:list')],
)
async def chat_with_resume(
    request: Request,
    chat_req: ResumeChatRequestModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> StreamingResponse:
    """
    简历智能问答（RAG模式）
    """
    user_id = current_user.user.user_id if current_user and current_user.user else 1
    chat_stream = ResumeKbService.chat_with_resume_services(query_db, chat_req, user_id)
    logger.info(f'用户{user_id}发起简历智能问答')

    return StreamingResponse(content=chat_stream, media_type='text/event-stream')
