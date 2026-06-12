import os
import urllib.parse
import json
from datetime import datetime
from typing import Annotated

from fastapi import Request, Response, Path, Query, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy import text

from module_admin.entity.do.resume_do import ResumeAttachment
from utils.file_util import UPLOAD_DIR

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, DynamicResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.resume_vo import (
    ResumeModel, ResumePageQueryModel, AddResumeModel, EditResumeModel,
    DeleteResumeModel, InterviewResultModel, ConfirmEntryModel,
    ResumeRecommendModel, ResumeEmailTemplateModel, AddEmailTemplateModel,
    EditEmailTemplateModel, DeleteEmailTemplateModel, EntryProjectModel,
    ResumeRecommendPageQueryModel, EmailTemplatePageQueryModel, ReleaseResumeModel,
    ResumeParseResultModel
)
from module_admin.service.resume_service import ResumeService
from module_email.service.mail_service import MailService
from exceptions.exception import ServiceException
from utils.log_util import logger
from utils.response_util import ResponseUtil


# 路由定义
resume_controller = APIRouterPro(
    prefix='/resume', order_num=101, tags=['简历库管理'], dependencies=[PreAuthDependency()]
)


class CurrentUserModel:
    """模拟当前用户模型"""
    user: object = None


def _to_camel_key(key: str) -> str:
    """将下划线命名转换为驼峰命名"""
    parts = key.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


@resume_controller.get(
    '/list',
    summary='获取简历分页列表接口',
    description='用于获取简历分页列表',
    response_model=PageResponseModel[ResumeModel],
    dependencies=[UserInterfaceAuthDependency('resume:resume:list')],
)
async def get_resume_list(
        request: Request,
        resume_page_query: Annotated[ResumePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取简历分页列表"""
    try:
        logger.info(f'获取简历列表，page_num={resume_page_query.page_num}, page_size={resume_page_query.page_size}')
        
        resume_page_query_result = await ResumeService.get_resume_list_services(
            query_db, resume_page_query, is_page=True
        )
        logger.info(f'获取简历列表成功，结果类型: {type(resume_page_query_result).__name__}')

        # 处理分页结果
        if isinstance(resume_page_query_result, dict) and 'rows' in resume_page_query_result:
            rows_data = resume_page_query_result.get('rows', [])
            processed_rows = []
            for item in rows_data:
                if hasattr(item, 'keys') and hasattr(item, '__getitem__'):
                    # 处理 dict 或 RowMapping 类型
                    row_dict = dict(item)
                    
                    # 先处理嵌套的 ResumeInfo 对象，将其展平到同一级
                    resume_info = None
                    for key in ['ResumeInfo', 'resumeInfo', 'resume_info']:
                        if key in row_dict:
                            resume_info = row_dict.pop(key)
                            break
                    
                    if resume_info:
                        if hasattr(resume_info, 'keys') and hasattr(resume_info, '__getitem__'):
                            resume_dict = dict(resume_info)
                            row_dict.update(resume_dict)
                        elif hasattr(resume_info, '__dict__'):
                            resume_dict = {k: v for k, v in resume_info.__dict__.items() if not k.startswith('_')}
                            row_dict.update(resume_dict)
                    
                    # 处理时间字段，将 T 替换为空格
                    for key, value in row_dict.items():
                        if isinstance(value, str) and 'T' in value:
                            row_dict[key] = value.replace('T', ' ')
                        elif hasattr(value, 'isoformat'):
                            row_dict[key] = value.isoformat().replace('T', ' ')
                    
                    # 下划线转驼峰
                    row_dict = {_to_camel_key(k): v for k, v in row_dict.items()}
                else:
                    row_dict = {'error': '数据转换失败'}
                processed_rows.append(row_dict)
            
            return ResponseUtil.success(
                rows=processed_rows,
                dict_content={
                    'total': resume_page_query_result.get('total', 0),
                    'pageNum': resume_page_query_result.get('pageNum', resume_page_query.page_num),
                    'pageSize': resume_page_query_result.get('pageSize', resume_page_query.page_size)
                }
            )
        elif isinstance(resume_page_query_result, list):
            # 列表结果：逐个处理
            processed_data = []
            for item in resume_page_query_result:
                if hasattr(item, 'model_dump'):
                    row_dict = item.model_dump(by_alias=True)
                    # 处理时间字段，将 T 替换为空格
                    for key, value in row_dict.items():
                        if isinstance(value, str) and 'T' in value:
                            row_dict[key] = value.replace('T', ' ')
                    processed_data.append(row_dict)
                else:
                    processed_data.append(item)
            return ResponseUtil.success(data=processed_data)
        else:
            # 其他类型：直接返回
            return ResponseUtil.success(data=resume_page_query_result)
    except ServiceException as e:
        logger.error(f'获取简历列表失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取简历列表失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取列表失败：{str(e)}')


@resume_controller.get(
    '/recommends',
    summary='获取简历推荐记录列表接口',
    description='用于获取简历的推荐记录列表，支持分页和多条件查询',
    response_model=PageResponseModel[ResumeRecommendModel],
    dependencies=[UserInterfaceAuthDependency('resume:resume:query')],
)
async def get_resume_recommend_list(
        request: Request,
        recommend_page_query: Annotated[ResumeRecommendPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取简历推荐记录列表（分页）"""
    try:
        logger.info(f'获取推荐记录列表，page_num={recommend_page_query.page_num}, page_size={recommend_page_query.page_size}')
        
        recommend_page_query_result = await ResumeService.get_resume_recommend_list_services(
            query_db, recommend_page_query, is_page=True
        )
        
        # 处理分页结果
        if isinstance(recommend_page_query_result, dict) and 'rows' in recommend_page_query_result:
            rows_data = recommend_page_query_result.get('rows', [])
            processed_rows = []
            for item in rows_data:
                if hasattr(item, 'model_dump'):
                    # 使用 by_alias=True 确保驼峰命名
                    row_dict = item.model_dump(by_alias=True)
                    # 处理时间字段，将 T 替换为空格
                    for key, value in row_dict.items():
                        if isinstance(value, str) and 'T' in value:
                            row_dict[key] = value.replace('T', ' ')
                elif isinstance(item, dict):
                    row_dict = item.copy()
                    # 处理时间字段，将 T 替换为空格
                    for key, value in row_dict.items():
                        if isinstance(value, str) and 'T' in value:
                            row_dict[key] = value.replace('T', ' ')
                else:
                    row_dict = {}
                    try:
                        for key in item.__dict__:
                            if not key.startswith('_'):
                                value = getattr(item, key)
                                # 将下划线命名转换为驼峰命名
                                camel_key = ''.join(word.capitalize() if i > 0 else word 
                                                   for i, word in enumerate(key.split('_')))
                                if hasattr(value, 'isoformat'):
                                    # 将 T 替换为空格
                                    row_dict[camel_key] = value.isoformat().replace('T', ' ')
                                else:
                                    row_dict[camel_key] = value
                    except:
                        row_dict = {'error': '数据转换失败'}
                processed_rows.append(row_dict)
            
            # 返回标准驼峰命名的分页结果
            page_info = {
                'rows': processed_rows,
                'total': recommend_page_query_result.get('total', 0),
                'pageNum': recommend_page_query_result.get('pageNum', recommend_page_query.page_num),
                'pageSize': recommend_page_query_result.get('pageSize', recommend_page_query.page_size),
                'hasNext': recommend_page_query_result.get('hasNext', False)
            }
            return ResponseUtil.success(dict_content=page_info)
        elif isinstance(recommend_page_query_result, list):
            processed_data = []
            for item in recommend_page_query_result:
                if hasattr(item, 'model_dump'):
                    row_dict = item.model_dump(by_alias=True)
                    # 处理时间字段，将 T 替换为空格
                    for key, value in row_dict.items():
                        if isinstance(value, str) and 'T' in value:
                            row_dict[key] = value.replace('T', ' ')
                    processed_data.append(row_dict)
                else:
                    processed_data.append(item)
            return ResponseUtil.success(data=processed_data)
        else:
            return ResponseUtil.success(data=recommend_page_query_result)
    except ServiceException as e:
        logger.error(f'获取推荐记录失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取推荐记录失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取失败：{str(e)}')


@resume_controller.get(
    '/{resume_id}',
    summary='获取简历详情接口',
    description='用于获取简历详细信息',
    response_model=DynamicResponseModel[ResumeModel],
    dependencies=[UserInterfaceAuthDependency('resume:resume:query')],
)
async def get_resume_detail(
        request: Request,
        resume_id: Annotated[int, Path(description='简历 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取简历详情"""
    try:
        resume_detail = await ResumeService.resume_detail_services(query_db, resume_id)
        
        # 构建结果字典，直接包含简历字段和 attachments
        result = {}
        
        if 'resume' in resume_detail:
            resume_info = resume_detail['resume']
            if hasattr(resume_info, 'model_dump'):
                # 使用 by_alias=True 确保驼峰命名
                resume_dict = resume_info.model_dump(by_alias=True)
                # 处理时间字段，将 T 替换为空格
                for key, value in resume_dict.items():
                    if isinstance(value, str) and 'T' in value:
                        resume_dict[key] = value.replace('T', ' ')
                result.update(resume_dict)
            elif isinstance(resume_info, dict):
                result.update(resume_info.copy())
            else:
                # 处理 ORM 对象
                for key in resume_info.__dict__:
                    if not key.startswith('_'):
                        value = getattr(resume_info, key)
                        # 将下划线命名转换为驼峰命名
                        camel_key = ''.join(word.capitalize() if i > 0 else word 
                                           for i, word in enumerate(key.split('_')))
                        if hasattr(value, 'isoformat'):
                            result[camel_key] = value.isoformat().replace('T', ' ')
                        else:
                            result[camel_key] = value
        
        # 添加 attachments 字段（驼峰命名）
        result['attachments'] = []
        if 'attachments' in resume_detail:
            for att in resume_detail['attachments']:
                att_dict = {}
                if hasattr(att, 'model_dump'):
                    raw_dict = att.model_dump()
                elif isinstance(att, dict):
                    raw_dict = att
                else:
                    # 处理 ORM 对象
                    raw_dict = {}
                    for key in att.__dict__:
                        if not key.startswith('_'):
                            raw_dict[key] = getattr(att, key)
                
                # 转换为驼峰命名
                for key, value in raw_dict.items():
                    camel_key = ''.join(word.capitalize() if i > 0 else word 
                                       for i, word in enumerate(key.split('_')))
                    if isinstance(value, str) and 'T' in value:
                        att_dict[camel_key] = value.replace('T', ' ')
                    elif hasattr(value, 'isoformat'):
                        att_dict[camel_key] = value.isoformat().replace('T', ' ')
                    else:
                        att_dict[camel_key] = value
                
                result['attachments'].append(att_dict)
        
        return ResponseUtil.success(data=result)
    except ServiceException as e:
        logger.error(f'获取简历详情失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取简历详情失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取详情失败：{str(e)}')


@resume_controller.post(
    '/add',
    summary='新增简历接口',
    description='用于新增简历',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:add')],
)
@Log(title='简历管理', business_type=BusinessType.INSERT)
async def add_resume(
        request: Request,
        add_resume: AddResumeModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """新增简历"""
    try:
        await ResumeService.add_resume_services(query_db, add_resume)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}新增简历成功')
        return ResponseUtil.success(msg='新增简历成功')
    except ServiceException as e:
        logger.error(f'新增简历失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'新增简历失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'新增失败：{str(e)}')


@resume_controller.post(
    '/upd',
    summary='编辑简历接口',
    description='用于编辑简历',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:edit')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def edit_resume(
        request: Request,
        edit_resume: EditResumeModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """编辑简历"""
    try:
        await ResumeService.edit_resume_services(query_db, edit_resume)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}编辑简历成功，ID：{edit_resume.id}')
        return ResponseUtil.success(msg='编辑简历成功')
    except ServiceException as e:
        logger.error(f'编辑简历失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'编辑简历失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'编辑失败：{str(e)}')


@resume_controller.delete(
    '/{ids}',
    summary='删除简历接口',
    description='用于删除简历',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:remove')],
)
@Log(title='简历管理', business_type=BusinessType.DELETE)
async def delete_resume(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的简历 ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """删除简历（软删除）"""
    try:
        delete_resume_obj = DeleteResumeModel(ids=ids)
        await ResumeService.delete_resume_services(query_db, delete_resume_obj)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}删除简历成功，ID：{ids}')
        return ResponseUtil.success(msg='删除简历成功')
    except ServiceException as e:
        logger.error(f'删除简历失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除简历失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'删除失败：{str(e)}')


@resume_controller.get(
    '/attachment/download/{attachment_id}',
    summary='下载简历附件接口',
    description='用于下载简历附件',
    dependencies=[UserInterfaceAuthDependency('resume:attachment:download')],
)
async def download_resume_attachment(
        request: Request,
        attachment_id: Annotated[int, Path(description='附件ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """下载简历附件"""
    try:
        # 查询附件信息
        query = select(ResumeAttachment).where(
            ResumeAttachment.id == attachment_id,
            ResumeAttachment.delete_time == 0
        )
        attachment = (await query_db.execute(query)).scalars().first()
        if attachment:
            attachment_info = {
                'id': attachment.id,
                'file_name': attachment.file_name,
                'file_path': attachment.file_path,
                'file_mime': attachment.file_mime,
                'resume_id': attachment.resume_id
            }
            logger.info(f'下载简历附件请求，附件信息：{json.dumps(attachment_info, ensure_ascii=False)}')
        if not attachment:
            logger.warning(f'附件不存在或已删除，ID：{attachment_id}')
            return ResponseUtil.error(msg='附件不存在或已删除')

        # 拼接绝对路径
        absolute_path = os.path.join(UPLOAD_DIR, attachment.file_path)
        
        # 记录文件地址和下载地址
        download_url = str(request.url)
        logger.info(f'下载简历附件请求，附件ID：{attachment_id}，文件地址：{absolute_path}，下载地址：{download_url}')
        
        if not os.path.exists(absolute_path):
            logger.error(f'附件文件不存在，路径：{absolute_path}')
            return ResponseUtil.error(msg='附件文件已被删除')

        # 处理中文文件名编码
        encoded_filename = urllib.parse.quote(attachment.file_name)

        # 返回文件响应
        response = FileResponse(
            path=absolute_path,
            media_type=attachment.file_mime or 'application/octet-stream',
            filename=attachment.file_name
        )
        response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"

        logger.info(f'下载附件成功，ID：{attachment_id}，文件名：{attachment.file_name}')
        return response
    except Exception as e:
        logger.error(f'下载附件失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'下载失败：{str(e)}')


@resume_controller.post(
    '/release',
    summary='释放简历接口',
    description='用于释放简历（修改简历状态）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:release')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def release_resume(
        request: Request,
        release_resume: ReleaseResumeModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """释放简历（修改状态）"""
    try:
        await ResumeService.release_resume_services(
            query_db, 
            resume_id=release_resume.resume_id, 
            status=release_resume.status
        )
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}释放简历成功，简历ID：{release_resume.resume_id}')
        return ResponseUtil.success(msg='释放成功')
    except ServiceException as e:
        logger.error(f'释放简历失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'释放简历失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'释放失败：{str(e)}')


@resume_controller.post(
    '/interview',
    summary='面试结果接口',
    description='用于更新面试结果（已通过/未通过）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:interview')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def interview_result(
        request: Request,
        interview_result: InterviewResultModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """面试结果处理"""
    try:
        result = await ResumeService.interview_result_services(query_db, interview_result)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}更新面试结果，简历ID：{interview_result.resume_id}，状态值：{interview_result.status}')
        return ResponseUtil.success(msg=result.message)
    except ServiceException as e:
        logger.error(f'更新面试结果失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'更新面试结果失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'更新失败：{str(e)}')


@resume_controller.post(
    '/entry',
    summary='确认入职接口',
    description='用于办理入职，创建员工账号',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:entry')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def confirm_entry(
        request: Request,
        confirm_entry: ConfirmEntryModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """确认入职"""
    try:
        result = await ResumeService.confirm_entry_services(query_db, confirm_entry)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}办理入职成功，简历ID：{confirm_entry.resume_id}，用户ID：{result.result.get("user_id")}')
        return ResponseUtil.success(msg='入职办理成功', data=result.result)
    except ServiceException as e:
        logger.error(f'入职办理失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'入职办理失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'入职失败：{str(e)}')


@resume_controller.post(
    '/recommend',
    summary='推荐简历到项目接口',
    description='用于将简历推荐到指定项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:recommend')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def recommend_resume(
        request: Request,
        recommend_resume: ResumeRecommendModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """推荐简历到项目"""
    try:
        # 设置推荐人信息
        recommend_resume.recommender_id = current_user.user.user_id if hasattr(current_user.user, 'user_id') else 0
        recommend_resume.recommender_name = current_user.user.nick_name if hasattr(current_user.user, 'nick_name') else ''
        
        await ResumeService.recommend_resume_services(query_db, recommend_resume)
        
        # 如果提供了邮箱地址和附件路径，发送带附件的邮件
        if recommend_resume.email_url and recommend_resume.file_path:
            try:
                project_display_name = recommend_resume.entry_project_name or recommend_resume.project_name or '未知项目'
                email_subject = f'简历推荐 - {project_display_name}'
                email_content = f'您好，\n\n附件为推荐简历，请查收。\n\n推荐人：{recommend_resume.recommender_name if recommend_resume.recommender_name else "未知"}\n项目名称：{project_display_name}'
                # 拼接文件绝对路径（与下载接口保持一致）
                absolute_file_path = os.path.join(UPLOAD_DIR, recommend_resume.file_path)
                if not os.path.exists(absolute_file_path):
                    logger.warning(f'简历推荐邮件附件不存在，路径：{absolute_file_path}')
                else:
                    await MailService.send_mail_with_attachment_service(
                        to_email=recommend_resume.email_url,
                        subject=email_subject,
                        content=email_content,
                        file_path=absolute_file_path,
                        is_html=False
                    )
                logger.info(f'简历推荐邮件发送成功，收件人：{recommend_resume.email_url}')
            except Exception as e:
                logger.warning(f'简历推荐邮件发送失败：{str(e)}')
        
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}推荐简历成功，简历ID：{recommend_resume.resume_id}，项目ID：{recommend_resume.project_id}')
        return ResponseUtil.success(msg='推荐成功')
    except ServiceException as e:
        logger.error(f'推荐简历失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'推荐简历失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'推荐失败：{str(e)}')


@resume_controller.post(
    '/entry-project',
    summary='入场项目接口',
    description='用于将简历人员入场到指定项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:entry')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def entry_project(
        request: Request,
        entry_project: EntryProjectModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """入场项目"""
    try:
        await ResumeService.entry_project_services(query_db, entry_project)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}办理入场成功，简历ID：{entry_project.resume_id}，项目ID：{entry_project.project_id}')
        return ResponseUtil.success(msg='入场成功')
    except ServiceException as e:
        logger.error(f'入场失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'入场失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'入场失败：{str(e)}')


# 邮件模板管理接口
email_template_controller = APIRouterPro(
    prefix='/resume/email-template', order_num=102, tags=['简历邮件模板管理'], dependencies=[PreAuthDependency()]
)


@email_template_controller.get(
    '/list',
    summary='获取邮件模板列表接口',
    description='用于获取邮件模板列表（分页）',
    response_model=PageResponseModel[ResumeEmailTemplateModel],
    dependencies=[UserInterfaceAuthDependency('resume:email_template:list')],
)
async def get_email_template_list(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        page_num: int = Query(1, description='页码', ge=1),
        page_size: int = Query(10, description='每页数量', ge=1),
) -> Response:
    """获取邮件模板列表（分页）"""
    try:
        # 直接执行SQL查询
        offset = (page_num - 1) * page_size
        
        # 查询总数
        count_sql = "SELECT COUNT(*) FROM resume_email_template"
        count_result = await query_db.execute(text(count_sql))
        total = count_result.scalar() or 0
        
        # 查询分页数据
        query_sql = """
            SELECT * FROM resume_email_template 
            ORDER BY is_default DESC, create_time DESC 
            LIMIT :limit OFFSET :offset
        """
        query_result = await query_db.execute(text(query_sql), {'limit': page_size, 'offset': offset})
        rows = query_result.mappings().all()
        
        # 转换为驼峰命名
        processed_rows = []
        for row in rows:
            row_dict = dict(row)
            camel_dict = {}
            for key, value in row_dict.items():
                # 下划线转驼峰
                camel_key = ''.join(word.capitalize() if i > 0 else word 
                                   for i, word in enumerate(key.split('_')))
                # 处理时间字段
                if isinstance(value, str) and 'T' in value:
                    camel_dict[camel_key] = value.replace('T', ' ')
                elif hasattr(value, 'isoformat'):
                    camel_dict[camel_key] = value.isoformat().replace('T', ' ')
                else:
                    camel_dict[camel_key] = value
            processed_rows.append(camel_dict)
        
        return ResponseUtil.success(
            rows=processed_rows,
            dict_content={
                'total': total,
                'pageNum': page_num,
                'pageSize': page_size
            }
        )
    except ServiceException as e:
        logger.error(f'获取邮件模板列表失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取邮件模板列表失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取失败：{str(e)}')


@email_template_controller.get(
    '/{template_id}',
    summary='获取邮件模板详情接口',
    description='用于获取邮件模板详细信息',
    response_model=DynamicResponseModel[ResumeEmailTemplateModel],
    dependencies=[UserInterfaceAuthDependency('resume:email_template:query')],
)
async def get_email_template_detail(
        request: Request,
        template_id: Annotated[int, Path(description='模板 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取邮件模板详情"""
    try:
        result = await ResumeService.get_email_template_detail_services(query_db, template_id)
        from utils.common_util import CamelCaseUtil
        processed_result = CamelCaseUtil.transform_result(result) if hasattr(CamelCaseUtil, 'transform_result') else result
        return ResponseUtil.success(data=processed_result)
    except ServiceException as e:
        logger.error(f'获取邮件模板详情失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取邮件模板详情失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取失败：{str(e)}')


@email_template_controller.post(
    '/add',
    summary='新增邮件模板接口',
    description='用于新增邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:add')],
)
@Log(title='邮件模板管理', business_type=BusinessType.INSERT)
async def add_email_template(
        request: Request,
        add_template: AddEmailTemplateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """新增邮件模板"""
    try:
        await ResumeService.add_email_template_services(query_db, add_template)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}新增邮件模板成功，模板名称：{add_template.template_name}')
        return ResponseUtil.success(msg='新增成功')
    except ServiceException as e:
        logger.error(f'新增邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'新增邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'新增失败：{str(e)}')


@email_template_controller.post(
    '/upd',
    summary='编辑邮件模板接口',
    description='用于编辑邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:edit')],
)
@Log(title='邮件模板管理', business_type=BusinessType.UPDATE)
async def edit_email_template(
        request: Request,
        edit_template: EditEmailTemplateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """编辑邮件模板"""
    try:
        await ResumeService.edit_email_template_services(query_db, edit_template)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}编辑邮件模板成功，模板ID：{edit_template.id}')
        return ResponseUtil.success(msg='修改成功')
    except ServiceException as e:
        logger.error(f'编辑邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'编辑邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'修改失败：{str(e)}')


@email_template_controller.delete(
    '/{ids}',
    summary='删除邮件模板接口',
    description='用于删除邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:remove')],
)
@Log(title='邮件模板管理', business_type=BusinessType.DELETE)
async def delete_email_template(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的模板 ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """删除邮件模板"""
    try:
        delete_template_obj = DeleteEmailTemplateModel(ids=ids)
        await ResumeService.delete_email_template_services(query_db, delete_template_obj)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}删除邮件模板成功，ID：{ids}')
        return ResponseUtil.success(msg='删除成功')
    except ServiceException as e:
        logger.error(f'删除邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'删除失败：{str(e)}')


@resume_controller.post(
    '/recommend',
    summary='推荐简历到项目接口',
    description='用于将简历推荐到指定项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:recommend')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def recommend_resume(
        request: Request,
        recommend_resume: ResumeRecommendModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """推荐简历到项目"""
    try:
        # 设置推荐人信息
        recommend_resume.recommender_id = current_user.user.user_id if hasattr(current_user.user, 'user_id') else 0
        recommend_resume.recommender_name = current_user.user.nick_name if hasattr(current_user.user, 'nick_name') else ''
        
        await ResumeService.recommend_resume_services(query_db, recommend_resume)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}推荐简历成功，简历ID：{recommend_resume.resume_id}，项目ID：{recommend_resume.project_id}')
        return ResponseUtil.success(msg='推荐成功')
    except ServiceException as e:
        logger.error(f'推荐简历失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'推荐简历失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'推荐失败：{str(e)}')


@resume_controller.post(
    '/entry-project',
    summary='入场项目接口',
    description='用于将简历人员入场到指定项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:entry')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def entry_project(
        request: Request,
        entry_project: EntryProjectModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """入场项目"""
    try:
        await ResumeService.entry_project_services(query_db, entry_project)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}办理入场成功，简历ID：{entry_project.resume_id}，项目ID：{entry_project.project_id}')
        return ResponseUtil.success(msg='入场成功')
    except ServiceException as e:
        logger.error(f'入场失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'入场失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'入场失败：{str(e)}')


# 邮件模板管理接口
email_template_controller = APIRouterPro(
    prefix='/resume/email-template', order_num=102, tags=['简历邮件模板管理'], dependencies=[PreAuthDependency()]
)


@email_template_controller.get(
    '/list',
    summary='获取邮件模板列表接口',
    description='用于获取邮件模板列表（分页）',
    response_model=PageResponseModel[ResumeEmailTemplateModel],
    dependencies=[UserInterfaceAuthDependency('resume:email_template:list')],
)
async def get_email_template_list(
        request: Request,
        email_template_page_query: Annotated[EmailTemplatePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取邮件模板列表（分页）"""
    try:
        result = await ResumeService.get_email_template_list_services(
            query_db, 
            page_num=email_template_page_query.page_num or 1, 
            page_size=email_template_page_query.page_size or 10
        )
        
        # 处理分页结果
        rows_data = result.get('rows', [])
        processed_rows = []
        for item in rows_data:
            if hasattr(item, 'model_dump'):
                # 使用 by_alias=True 确保驼峰命名
                row_dict = item.model_dump(by_alias=True)
                # 处理时间字段，将 T 替换为空格
                for key, value in row_dict.items():
                    if isinstance(value, str) and 'T' in value:
                        row_dict[key] = value.replace('T', ' ')
                processed_rows.append(row_dict)
            elif isinstance(item, dict):
                processed_rows.append(item)
            else:
                processed_rows.append(item.__dict__)
        
        page_info = {
            'rows': processed_rows,
            'total': result.get('total', 0),
            'pageNum': result.get('page_num', email_template_page_query.page_num or 1),
            'pageSize': result.get('page_size', email_template_page_query.page_size or 10)
        }
        
        return ResponseUtil.success(dict_content=page_info)
    except ServiceException as e:
        logger.error(f'获取邮件模板列表失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取邮件模板列表失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取失败：{str(e)}')


@email_template_controller.get(
    '/{template_id}',
    summary='获取邮件模板详情接口',
    description='用于获取邮件模板详细信息',
    response_model=DynamicResponseModel[ResumeEmailTemplateModel],
    dependencies=[UserInterfaceAuthDependency('resume:email_template:query')],
)
async def get_email_template_detail(
        request: Request,
        template_id: Annotated[int, Path(description='模板 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取邮件模板详情"""
    try:
        result = await ResumeService.get_email_template_detail_services(query_db, template_id)
        from utils.common_util import CamelCaseUtil
        processed_result = CamelCaseUtil.transform_result(result) if hasattr(CamelCaseUtil, 'transform_result') else result
        return ResponseUtil.success(data=processed_result)
    except ServiceException as e:
        logger.error(f'获取邮件模板详情失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取邮件模板详情失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取失败：{str(e)}')


@email_template_controller.post(
    '/add',
    summary='新增邮件模板接口',
    description='用于新增邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:add')],
)
@Log(title='邮件模板管理', business_type=BusinessType.INSERT)
async def add_email_template(
        request: Request,
        add_template: AddEmailTemplateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """新增邮件模板"""
    try:
        await ResumeService.add_email_template_services(query_db, add_template)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}新增邮件模板成功，模板名称：{add_template.template_name}')
        return ResponseUtil.success(msg='新增成功')
    except ServiceException as e:
        logger.error(f'新增邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'新增邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'新增失败：{str(e)}')


@email_template_controller.post(
    '/upd',
    summary='编辑邮件模板接口',
    description='用于编辑邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:edit')],
)
@Log(title='邮件模板管理', business_type=BusinessType.UPDATE)
async def edit_email_template(
        request: Request,
        edit_template: EditEmailTemplateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """编辑邮件模板"""
    try:
        await ResumeService.edit_email_template_services(query_db, edit_template)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}编辑邮件模板成功，模板ID：{edit_template.id}')
        return ResponseUtil.success(msg='修改成功')
    except ServiceException as e:
        logger.error(f'编辑邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'编辑邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'修改失败：{str(e)}')


@email_template_controller.delete(
    '/{ids}',
    summary='删除邮件模板接口',
    description='用于删除邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:remove')],
)
@Log(title='邮件模板管理', business_type=BusinessType.DELETE)
async def delete_email_template(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的模板 ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """删除邮件模板"""
    try:
        delete_template_obj = DeleteEmailTemplateModel(ids=ids)
        await ResumeService.delete_email_template_services(query_db, delete_template_obj)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}删除邮件模板成功，ID：{ids}')
        return ResponseUtil.success(msg='删除成功')
    except ServiceException as e:
        logger.error(f'删除邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'删除失败：{str(e)}')


@resume_controller.post(
    '/recommend',
    summary='推荐简历到项目接口',
    description='用于将简历推荐到指定项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:recommend')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def recommend_resume(
        request: Request,
        recommend_resume: ResumeRecommendModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """推荐简历到项目"""
    try:
        # 设置推荐人信息
        recommend_resume.recommender_id = current_user.user.user_id if hasattr(current_user.user, 'user_id') else 0
        recommend_resume.recommender_name = current_user.user.nick_name if hasattr(current_user.user, 'nick_name') else ''
        
        await ResumeService.recommend_resume_services(query_db, recommend_resume)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}推荐简历成功，简历ID：{recommend_resume.resume_id}，项目ID：{recommend_resume.project_id}')
        return ResponseUtil.success(msg='推荐成功')
    except ServiceException as e:
        logger.error(f'推荐简历失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'推荐简历失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'推荐失败：{str(e)}')


@resume_controller.post(
    '/entry-project',
    summary='入场项目接口',
    description='用于将简历人员入场到指定项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:entry')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def entry_project(
        request: Request,
        entry_project: EntryProjectModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """入场项目"""
    try:
        await ResumeService.entry_project_services(query_db, entry_project)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}办理入场成功，简历ID：{entry_project.resume_id}，项目ID：{entry_project.project_id}')
        return ResponseUtil.success(msg='入场成功')
    except ServiceException as e:
        logger.error(f'入场失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'入场失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'入场失败：{str(e)}')


# 邮件模板管理接口
email_template_controller = APIRouterPro(
    prefix='/resume/email-template', order_num=102, tags=['简历邮件模板管理'], dependencies=[PreAuthDependency()]
)


@email_template_controller.get(
    '/list',
    summary='获取邮件模板列表接口',
    description='用于获取邮件模板列表',
    response_model=DataResponseModel[ResumeEmailTemplateModel],
    dependencies=[UserInterfaceAuthDependency('resume:email_template:list')],
)
async def get_email_template_list(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取邮件模板列表"""
    try:
        result = await ResumeService.get_email_template_list_services(query_db)
        processed_data = [
            item.model_dump(by_alias=True) if hasattr(item, 'model_dump') else item
            for item in result
        ]
        return ResponseUtil.success(data=processed_data)
    except ServiceException as e:
        logger.error(f'获取邮件模板列表失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取邮件模板列表失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取失败：{str(e)}')


@email_template_controller.get(
    '/{template_id}',
    summary='获取邮件模板详情接口',
    description='用于获取邮件模板详细信息',
    response_model=DynamicResponseModel[ResumeEmailTemplateModel],
    dependencies=[UserInterfaceAuthDependency('resume:email_template:query')],
)
async def get_email_template_detail(
        request: Request,
        template_id: Annotated[int, Path(description='模板 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取邮件模板详情"""
    try:
        result = await ResumeService.get_email_template_detail_services(query_db, template_id)
        from utils.common_util import CamelCaseUtil
        processed_result = CamelCaseUtil.transform_result(result) if hasattr(CamelCaseUtil, 'transform_result') else result
        return ResponseUtil.success(data=processed_result)
    except ServiceException as e:
        logger.error(f'获取邮件模板详情失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取邮件模板详情失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取失败：{str(e)}')


@email_template_controller.post(
    '/add',
    summary='新增邮件模板接口',
    description='用于新增邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:add')],
)
@Log(title='邮件模板管理', business_type=BusinessType.INSERT)
async def add_email_template(
        request: Request,
        add_template: AddEmailTemplateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """新增邮件模板"""
    try:
        await ResumeService.add_email_template_services(query_db, add_template)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}新增邮件模板成功，模板名称：{add_template.template_name}')
        return ResponseUtil.success(msg='新增成功')
    except ServiceException as e:
        logger.error(f'新增邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'新增邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'新增失败：{str(e)}')


@email_template_controller.post(
    '/upd',
    summary='编辑邮件模板接口',
    description='用于编辑邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:edit')],
)
@Log(title='邮件模板管理', business_type=BusinessType.UPDATE)
async def edit_email_template(
        request: Request,
        edit_template: EditEmailTemplateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """编辑邮件模板"""
    try:
        await ResumeService.edit_email_template_services(query_db, edit_template)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}编辑邮件模板成功，模板ID：{edit_template.id}')
        return ResponseUtil.success(msg='修改成功')
    except ServiceException as e:
        logger.error(f'编辑邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'编辑邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'修改失败：{str(e)}')


@email_template_controller.delete(
    '/{ids}',
    summary='删除邮件模板接口',
    description='用于删除邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:remove')],
)
@Log(title='邮件模板管理', business_type=BusinessType.DELETE)
async def delete_email_template(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的模板 ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """删除邮件模板"""
    try:
        delete_template_obj = DeleteEmailTemplateModel(ids=ids)
        await ResumeService.delete_email_template_services(query_db, delete_template_obj)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}删除邮件模板成功，ID：{ids}')
        return ResponseUtil.success(msg='删除成功')
    except ServiceException as e:
        logger.error(f'删除邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'删除失败：{str(e)}')


@resume_controller.post(
    '/recommend',
    summary='推荐简历到项目接口',
    description='用于将简历推荐到指定项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:recommend')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def recommend_resume(
        request: Request,
        recommend_resume: ResumeRecommendModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """推荐简历到项目"""
    try:
        # 设置推荐人信息
        recommend_resume.recommender_id = current_user.user.user_id if hasattr(current_user.user, 'user_id') else 0
        recommend_resume.recommender_name = current_user.user.nick_name if hasattr(current_user.user, 'nick_name') else ''
        
        await ResumeService.recommend_resume_services(query_db, recommend_resume)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}推荐简历成功，简历ID：{recommend_resume.resume_id}，项目ID：{recommend_resume.project_id}')
        return ResponseUtil.success(msg='推荐成功')
    except ServiceException as e:
        logger.error(f'推荐简历失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'推荐简历失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'推荐失败：{str(e)}')


@resume_controller.post(
    '/entry-project',
    summary='入场项目接口',
    description='用于将简历人员入场到指定项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:resume:entry')],
)
@Log(title='简历管理', business_type=BusinessType.UPDATE)
async def entry_project(
        request: Request,
        entry_project: EntryProjectModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """入场项目"""
    try:
        await ResumeService.entry_project_services(query_db, entry_project)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}办理入场成功，简历ID：{entry_project.resume_id}，项目ID：{entry_project.project_id}')
        return ResponseUtil.success(msg='入场成功')
    except ServiceException as e:
        logger.error(f'入场失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'入场失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'入场失败：{str(e)}')


# 邮件模板管理接口
email_template_controller = APIRouterPro(
    prefix='/resume/email-template', order_num=102, tags=['简历邮件模板管理'], dependencies=[PreAuthDependency()]
)


@email_template_controller.get(
    '/list',
    summary='获取邮件模板列表接口',
    description='用于获取邮件模板列表',
    response_model=DataResponseModel[ResumeEmailTemplateModel],
    dependencies=[UserInterfaceAuthDependency('resume:email_template:list')],
)
async def get_email_template_list(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取邮件模板列表"""
    try:
        result = await ResumeService.get_email_template_list_services(query_db)
        processed_data = [
            item.model_dump(by_alias=True) if hasattr(item, 'model_dump') else item
            for item in result
        ]
        return ResponseUtil.success(data=processed_data)
    except ServiceException as e:
        logger.error(f'获取邮件模板列表失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取邮件模板列表失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取失败：{str(e)}')


@email_template_controller.get(
    '/{template_id}',
    summary='获取邮件模板详情接口',
    description='用于获取邮件模板详细信息',
    response_model=DynamicResponseModel[ResumeEmailTemplateModel],
    dependencies=[UserInterfaceAuthDependency('resume:email_template:query')],
)
async def get_email_template_detail(
        request: Request,
        template_id: Annotated[int, Path(description='模板 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取邮件模板详情"""
    try:
        result = await ResumeService.get_email_template_detail_services(query_db, template_id)
        from utils.common_util import CamelCaseUtil
        processed_result = CamelCaseUtil.transform_result(result) if hasattr(CamelCaseUtil, 'transform_result') else result
        return ResponseUtil.success(data=processed_result)
    except ServiceException as e:
        logger.error(f'获取邮件模板详情失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取邮件模板详情失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取失败：{str(e)}')


@email_template_controller.post(
    '/add',
    summary='新增邮件模板接口',
    description='用于新增邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:add')],
)
@Log(title='邮件模板管理', business_type=BusinessType.INSERT)
async def add_email_template(
        request: Request,
        add_template: AddEmailTemplateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """新增邮件模板"""
    try:
        await ResumeService.add_email_template_services(query_db, add_template)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}新增邮件模板成功，模板名称：{add_template.template_name}')
        return ResponseUtil.success(msg='新增成功')
    except ServiceException as e:
        logger.error(f'新增邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'新增邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'新增失败：{str(e)}')


@email_template_controller.post(
    '/upd',
    summary='编辑邮件模板接口',
    description='用于编辑邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:edit')],
)
@Log(title='邮件模板管理', business_type=BusinessType.UPDATE)
async def edit_email_template(
        request: Request,
        edit_template: EditEmailTemplateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """编辑邮件模板"""
    try:
        await ResumeService.edit_email_template_services(query_db, edit_template)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}编辑邮件模板成功，模板ID：{edit_template.id}')
        return ResponseUtil.success(msg='修改成功')
    except ServiceException as e:
        logger.error(f'编辑邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'编辑邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'修改失败：{str(e)}')


@email_template_controller.delete(
    '/{ids}',
    summary='删除邮件模板接口',
    description='用于删除邮件模板',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('resume:email_template:remove')],
)
@Log(title='邮件模板管理', business_type=BusinessType.DELETE)
async def delete_email_template(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的模板 ID，多个用逗号分隔')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """删除邮件模板"""
    try:
        delete_template_obj = DeleteEmailTemplateModel(ids=ids)
        await ResumeService.delete_email_template_services(query_db, delete_template_obj)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}删除邮件模板成功，ID：{ids}')
        return ResponseUtil.success(msg='删除成功')
    except ServiceException as e:
        logger.error(f'删除邮件模板失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'删除邮件模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'删除失败：{str(e)}')

@resume_controller.get(
    '/template/download',
    summary='下载简历模板接口',
    description='用于下载简历模板文件',
    dependencies=[UserInterfaceAuthDependency('resume:resume:download')],
)
async def download_resume_template(
        request: Request,
) -> Response:
    """下载简历模板文件"""
    try:
        # 简历模板文件路径
        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'resume_template', '简历模版.docx')

        # 记录文件地址和下载地址
        download_url = str(request.url)
        logger.info(f'下载简历模板请求，文件地址：{template_path}，下载地址：{download_url}')

        if not os.path.exists(template_path):
            logger.error(f'简历模板文件不存在，路径：{template_path}')
            return ResponseUtil.error(msg='简历模板文件不存在')

        # 处理中文文件名编码
        filename = '简历模版.docx'
        encoded_filename = urllib.parse.quote(filename)

        # 返回文件响应
        response = FileResponse(
            path=template_path,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=filename
        )
        response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"

        logger.info(f'下载简历模板成功，文件名：{filename}')
        return response
    except Exception as e:
        logger.error(f'下载简历模板失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'下载失败：{str(e)}')


@resume_controller.post(
    '/parse',
    summary='上传并解析简历接口',
    description='用于上传简历文件（Word/PDF）并解析其中的姓名、性别、年龄、毕业院校等信息',
    response_model=ResponseBaseModel,
)
async def parse_resume(
        request: Request,
        file: UploadFile = File(description='简历文件（Word或PDF格式）'),
) -> Response:
    """上传并解析简历"""
    try:
        from utils.resume_parser import ResumeParser
        import uuid
        
        # 验证文件类型
        file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if file_ext not in ['docx', 'pdf']:
            return ResponseUtil.error(msg='仅支持 Word(.docx) 和 PDF 格式的简历文件')
        
        # 读取上传的文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 保存到临时目录用于解析
        temp_dir = os.path.join(UPLOAD_DIR, 'temp_parse')
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f'{uuid.uuid4()}.{file_ext}')
        
        with open(temp_file_path, 'wb') as f:
            f.write(file_content)
        
        try:
            # 根据文件类型解析简历
            if file_ext == 'docx':
                parse_result = ResumeParser.parse_word_resume(temp_file_path)
            elif file_ext == 'pdf':
                parse_result = ResumeParser.parse_pdf_resume(temp_file_path)
            else:
                return ResponseUtil.error(msg='不支持的文件格式')
            
            # 保存文件到永久存储目录
            date_dir = datetime.now().strftime("%Y%m%d")
            save_dir = os.path.join(UPLOAD_DIR, 'resume', date_dir)
            os.makedirs(save_dir, exist_ok=True)
            unique_filename = f'{uuid.uuid4()}.{file_ext}'
            relative_path = os.path.join('resume', date_dir, unique_filename)
            absolute_path = os.path.join(save_dir, unique_filename)
            
            with open(absolute_path, 'wb') as f:
                f.write(file_content)
            
            # 构建文件信息（驼峰命名）
            file_info = {
                'name': parse_result.get('name'),
                'sex': parse_result.get('sex'),
                'age': parse_result.get('age'),
                'graduateSchool': parse_result.get('graduate_school'),
                'phone': parse_result.get('phone'),
                'email': parse_result.get('email'),
                'workYears': parse_result.get('work_years'),
                'fileName': file.filename,
                'filePath': relative_path,
                'fileSize': file_size,
                'fileExt': file_ext,
                'fileMime': file.content_type or 'application/octet-stream',
            }
            
            logger.info(f'简历解析成功，文件名：{file.filename}')
            return ResponseUtil.success(data=file_info, msg='解析成功')
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f'简历解析失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'解析失败：{str(e)}')