from datetime import datetime
from typing import Annotated

from fastapi import Request, Response, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, DynamicResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.resume_vo import (
    ResumeModel, ResumePageQueryModel, AddResumeModel, EditResumeModel,
    DeleteResumeModel, InterviewResultModel, ConfirmEntryModel
)
from module_admin.service.resume_service import ResumeService
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
                if hasattr(item, 'model_dump'):
                    row_dict = item.model_dump(by_alias=True)
                elif isinstance(item, dict):
                    row_dict = item.copy()
                else:
                    row_dict = {}
                    try:
                        for key in item.__dict__:
                            value = getattr(item, key)
                            if hasattr(value, 'isoformat'):
                                row_dict[key] = value.isoformat()
                            else:
                                row_dict[key] = value
                    except:
                        row_dict = {'error': '数据转换失败'}
                processed_rows.append(row_dict)
            
            page_info = {
                'rows': processed_rows,
                'total': resume_page_query_result.get('total', 0),
                'pageNum': resume_page_query_result.get('pageNum', resume_page_query.page_num),
                'pageSize': resume_page_query_result.get('pageSize', resume_page_query.page_size),
                'hasNext': resume_page_query_result.get('hasNext', False)
            }
            return ResponseUtil.success(dict_content=page_info)
        elif isinstance(resume_page_query_result, list):
            # 列表结果：逐个处理
            processed_data = [
                item.model_dump(by_alias=True) if hasattr(item, 'model_dump')
                else item
                for item in resume_page_query_result
            ]
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
        from utils.common_util import CamelCaseUtil
        result = {}
        if 'resume' in resume_detail:
            result['resume'] = CamelCaseUtil.transform_result(resume_detail['resume']) if hasattr(CamelCaseUtil, 'transform_result') else resume_detail['resume']
        if 'attachments' in resume_detail:
            result['attachments'] = [
                CamelCaseUtil.transform_result(att) if hasattr(CamelCaseUtil, 'transform_result') else att
                for att in resume_detail['attachments']
            ]
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
        await ResumeService.interview_result_services(query_db, interview_result)
        logger.info(f'用户{current_user.user.user_name if hasattr(current_user.user, "user_name") else "unknown"}更新面试结果，简历ID：{interview_result.resume_id}，结果：{interview_result.result}')
        return ResponseUtil.success(msg=f'面试结果已更新为{interview_result.result}')
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