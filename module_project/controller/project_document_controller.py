from typing import Annotated

from fastapi import Path, Query, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_project.entity.vo.project_document_vo import (
    AddProjectDocumentModel,
    DeleteProjectDocumentModel,
    EditProjectDocumentModel,
    ProjectDocumentModel,
    ProjectDocumentPageQueryModel,
)
from module_project.service.project_document_service import ProjectDocumentService
from utils.log_util import logger
from utils.response_util import ResponseUtil

project_document_controller = APIRouterPro(
    prefix='/project/document', order_num=21, tags=['项目管理 - 文档管理'], dependencies=[PreAuthDependency()]
)


@project_document_controller.get(
    '/list',
    summary='获取项目文档分页列表接口',
    description='用于获取项目文档分页列表',
    dependencies=[UserInterfaceAuthDependency('project:document:list')],
)
async def get_project_document_list(
        request: Request,
        project_document_page_query: Annotated[ProjectDocumentPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取项目文档列表（使用原生SQL）
    
    :param request: Request 对象
    :param project_document_page_query: 查询参数
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 文档列表
    """
    from sqlalchemy import text
    from utils.common_util import CamelCaseUtil
    
    # 分页参数
    page_num = project_document_page_query.page_num if project_document_page_query.page_num else 1
    page_size = project_document_page_query.page_size if project_document_page_query.page_size else 10
    offset = (page_num - 1) * page_size
    
    # 当前用户信息
    user_id = current_user.user.user_id
    is_admin = current_user.user.admin
    
    # 构建 WHERE 条件
    conditions = ["d.delete_time = 0"]
    params = {}
    
    # 关键词搜索
    if project_document_page_query.keywords:
        conditions.append("(d.title LIKE :keywords OR d.content LIKE :keywords)")
        params['keywords'] = f"%{project_document_page_query.keywords}%"
    
    # 项目ID筛选
    if project_document_page_query.project_id:
        conditions.append("d.project_id = :project_id")
        params['project_id'] = project_document_page_query.project_id
    else:
        # 如果没有指定项目ID，非管理员只能看自己的
        if not is_admin:
            conditions.append("d.admin_id = :user_id")
            params['user_id'] = user_id
    
    where_clause = " AND ".join(conditions)
    
    # 构建完整 SQL 查询
    sql = text(f"""
        SELECT 
            d.id,
            d.title,
            d.project_id AS projectId,
            d.content,
            d.file_ids AS fileIds,
            d.admin_id AS adminId,
            d.create_time AS createTime,
            d.update_time AS updateTime,
            d.delete_time AS deleteTime,
            p.name AS projectName,
            u.nick_name AS adminName,
            u.user_name AS userName,
            FROM_UNIXTIME(d.create_time, '%Y-%m-%d %H:%i:%s') AS createTimeStr,
            FROM_UNIXTIME(d.update_time, '%Y-%m-%d %H:%i:%s') AS updateTimeStr
        FROM oa_project_document d
        LEFT JOIN oa_project p ON d.project_id = p.id
        LEFT JOIN sys_user u ON d.admin_id = u.user_id
        WHERE {where_clause}
        ORDER BY d.create_time DESC
        LIMIT :limit OFFSET :offset
    """)
    
    # 执行总数查询
    count_sql = text(f"""
        SELECT COUNT(*) as total
        FROM oa_project_document d
        LEFT JOIN oa_project p ON d.project_id = p.id
        LEFT JOIN sys_user u ON d.admin_id = u.user_id
        WHERE {where_clause}
    """)
    
    # 添加分页参数
    params['limit'] = page_size
    params['offset'] = offset
    
    # 执行总数查询
    count_result = await query_db.execute(count_sql, params)
    total = count_result.scalar()
    
    # 执行分页查询
    result = await query_db.execute(sql, params)
    rows = result.mappings().all()
    
    # 转换为字典列表并处理数据类型
    document_list = []
    for row in rows:
        doc_dict = dict(row)
        
        # 处理数值类型
        for key in ['id', 'projectId', 'adminId', 'createTime', 'updateTime', 'deleteTime']:
            if key in doc_dict and doc_dict[key] is not None:
                doc_dict[key] = int(doc_dict[key])
        
        # 处理字符串默认值
        if 'fileIds' not in doc_dict or doc_dict['fileIds'] is None:
            doc_dict['fileIds'] = ""
        if 'content' not in doc_dict or doc_dict['content'] is None:
            doc_dict['content'] = ""
        if 'projectName' not in doc_dict or doc_dict['projectName'] is None:
            doc_dict['projectName'] = ""
        if 'adminName' not in doc_dict or doc_dict['adminName'] is None:
            doc_dict['adminName'] = ""
        if 'userName' not in doc_dict or doc_dict['userName'] is None:
            doc_dict['userName'] = ""
        if 'createTimeStr' not in doc_dict or doc_dict['createTimeStr'] is None:
            doc_dict['createTimeStr'] = ""
        if 'updateTimeStr' not in doc_dict or doc_dict['updateTimeStr'] is None:
            doc_dict['updateTimeStr'] = ""
        
        document_list.append(doc_dict)
    
    # 计算是否有下一页
    has_next = page_num * page_size < total
    
    response_data = {
        'rows': document_list,
        'total': total,
        'pageNum': page_num,
        'pageSize': page_size,
        'hasNext': has_next
    }
    
    logger.info(f'获取项目文档列表成功，共 {total} 条记录')
    
    return ResponseUtil.success(rows=document_list, dict_content={'total': total, 'pageNum': page_num, 'pageSize': page_size, 'hasNext': has_next})


@project_document_controller.post(
    '',
    summary='新增项目文档接口',
    description='用于新增项目文档',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:document:add')],
)
@ValidateFields(validate_model='add_project_document')
@Log(title='项目文档管理', business_type=BusinessType.INSERT)
async def add_project_document(
        request: Request,
        add_project_document: AddProjectDocumentModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_project_document_result = await ProjectDocumentService.add_project_document_services(
        request, query_db, add_project_document, current_user.user.user_id
    )
    logger.info(add_project_document_result.message)

    return ResponseUtil.success(msg=add_project_document_result.message)


@project_document_controller.put(
    '',
    summary='编辑项目文档接口',
    description='用于编辑项目文档',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:document:edit')],
)
@ValidateFields(validate_model='edit_project_document')
@Log(title='项目文档管理', business_type=BusinessType.UPDATE)
async def edit_project_document(
        request: Request,
        edit_project_document: EditProjectDocumentModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_project_document_result = await ProjectDocumentService.edit_project_document_services(
        request, query_db, edit_project_document, current_user.user.user_id
    )
    logger.info(edit_project_document_result.message)

    return ResponseUtil.success(msg=edit_project_document_result.message)


@project_document_controller.delete(
    '/{id}',
    summary='删除项目文档接口',
    description='用于删除项目文档',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('project:document:remove')],
)
@Log(title='项目文档管理', business_type=BusinessType.DELETE)
async def delete_project_document(
        request: Request,
        id: Annotated[int, Path(description='需要删除的文档 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    delete_project_document = DeleteProjectDocumentModel(id=id)
    delete_project_document_result = await ProjectDocumentService.delete_project_document_services(
        request, query_db, delete_project_document, current_user.user.user_id
    )
    logger.info(delete_project_document_result.message)

    return ResponseUtil.success(msg=delete_project_document_result.message)


@project_document_controller.get(
    '/{id}',
    summary='获取项目文档详情接口',
    description='用于获取指定项目文档的详细信息',
    response_model=DataResponseModel[ProjectDocumentModel],
    dependencies=[UserInterfaceAuthDependency('project:document:query')],
)
async def query_project_document_detail(
        request: Request,
        id: Annotated[int, Path(description='文档 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_project_document_result = await ProjectDocumentService.project_document_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_project_document_result)
