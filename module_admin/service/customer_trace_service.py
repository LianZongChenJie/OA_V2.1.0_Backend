# 4. 创建 Service 文件：module_admin/service/customer_trace_service.py
import json
import os
import urllib.parse
from datetime import datetime
from typing import Any

from fastapi import Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.customer_trace_dao import CustomerTraceDao
from module_admin.entity.do.customer_do import OaCustomer
from module_admin.entity.do.customer_trace_do import CustomerTrace
from module_admin.entity.do.oa_admin_do import OaAdmin
from module_admin.entity.vo.customer_trace_vo import (
    TRACE_EXTEND_FIELDS,
    AddCustomerTraceModel,
    DeleteCustomerTraceModel,
    EditCustomerTraceModel,
    CustomerTraceModel,
    CustomerTracePageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.dict_service import DictDataService
from utils.common_util import CamelCaseUtil
from utils.file_util import UPLOAD_DIR
from utils.time_format_util import timestamp_to_datetime


class CustomerTraceService:
    """
    客户跟进记录管理服务层
    """

    @classmethod
    async def get_customer_trace_list_services(
            cls, request: Request, query_db: AsyncSession, query_object: CustomerTracePageQueryModel,
            current_user: CurrentUserModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取客户跟进记录列表信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param current_user: 当前登录用户对象
        :param is_page: 是否开启分页
        :return: 客户跟进记录列表信息对象
        """
        trace_list_result = await CustomerTraceDao.get_customer_trace_list(
            query_db, query_object, current_user.user.user_id, is_page
        )

        rows: list[dict[str, Any]] = (
            trace_list_result.rows if is_page and hasattr(trace_list_result, 'rows') else trace_list_result
        )
        if not rows:
            return trace_list_result

        await cls._enrich_trace_rows(request, query_db, rows)

        return trace_list_result

    @classmethod
    async def get_customer_trace_list_by_cid_services(
            cls, request: Request, query_db: AsyncSession, cid: int
    ) -> list[dict[str, Any]]:
        """
        获取指定客户的全部跟进记录 service（不过滤创建人，用于废弃客户详情场景）

        :param request: Request 对象
        :param query_db: orm 对象
        :param cid: 客户 ID
        :return: 该客户全部未删除的跟进记录列表
        """
        trace_list = (
            (await query_db.execute(
                select(CustomerTrace)
                .where(CustomerTrace.cid == cid, CustomerTrace.delete_time == 0)
                .order_by(CustomerTrace.follow_time.desc(), CustomerTrace.id.desc())
            )).scalars().all()
        )
        if not trace_list:
            return []

        # 与列表接口保持一致的字段命名（小驼峰）
        rows: list[dict[str, Any]] = [CamelCaseUtil.transform_result(item) for item in trace_list]
        await cls._enrich_trace_rows(request, query_db, rows)

        return rows

    @classmethod
    async def _enrich_trace_rows(
            cls, request: Request, query_db: AsyncSession, rows: list[dict[str, Any]]
    ) -> None:
        """
        批量组装跟进记录列表的展示字段（名称关联、字典翻译、时间格式化、附件解析）

        :param request: Request 对象
        :param query_db: orm 对象
        :param rows: 待组装的跟进记录字典列表（原地修改）
        :return:
        """
        # 收集当前页关联 ID，批量查询后内存组装，避免 N+1
        cids = {row.get('cid') for row in rows if row.get('cid')}
        contact_ids = {row.get('contactId') for row in rows if row.get('contactId')}
        admin_ids = {row.get('adminId') for row in rows if row.get('adminId')}

        customer_name_map: dict[int, str] = {}
        if cids:
            customer_rows = (
                await query_db.execute(select(OaCustomer.id, OaCustomer.name).where(OaCustomer.id.in_(cids)))
            ).all()
            customer_name_map = {row[0]: row[1] or '' for row in customer_rows}

        # 「联系人」前端数据源已切换为员工列表（「归属员工」同一接口），故按员工 ID 关联用户表昵称
        contact_name_map: dict[int, str] = {}
        if contact_ids:
            contact_rows = (
                await query_db.execute(
                    select(OaAdmin.id, OaAdmin.nickname).where(OaAdmin.id.in_(contact_ids))
                )
            ).all()
            contact_name_map = {row[0]: row[1] or '' for row in contact_rows}

        admin_name_map: dict[int, str] = {}
        if admin_ids:
            admin_rows = (
                await query_db.execute(
                    select(OaAdmin.id, OaAdmin.nickname).where(OaAdmin.id.in_(admin_ids))
                )
            ).all()
            admin_name_map = {row[0]: row[1] or '' for row in admin_rows}
        # 字典翻译
        follow_type_list = await DictDataService.query_dict_data_list_from_cache_services(
            request.app.state.redis, dict_type='customer_follow_type'
        )
        follow_type_map = {str(item.get('dictValue')): item.get('dictLabel') for item in follow_type_list}
        stage_list = await DictDataService.query_dict_data_list_from_cache_services(
            request.app.state.redis, dict_type='customer_trace_stage'
        )
        stage_map = {str(item.get('dictValue')): item.get('dictLabel') for item in stage_list}

        for row in rows:
            row['customerName'] = customer_name_map.get(row.get('cid') or 0, '')
            row['contactName'] = contact_name_map.get(row.get('contactId') or 0, '')
            row['typesName'] = follow_type_map.get(str(row.get('types') or ''), '')
            row['stageName'] = stage_map.get(str(row.get('stage') or ''), '')
            row['adminName'] = admin_name_map.get(row.get('adminId') or 0, '')
            row['followTimeStr'] = timestamp_to_datetime(row.get('followTime')) if row.get('followTime') else ''
            row['nextTimeStr'] = timestamp_to_datetime(row.get('nextTime')) if row.get('nextTime') else ''
            row['attachments'] = cls._parse_attachment_list(row.get('fileIds'))

    @classmethod
    def _parse_attachment_list(cls, file_ids: str | None) -> list[dict[str, Any]]:
        """
        解析附件 JSON 字符串为列表

        :param file_ids: 附件 JSON 字符串（形如 [{"fileName","filePath","fileSize","fileExt","fileMime"}]）
        :return: 附件列表
        """
        if not file_ids:
            return []
        try:
            attachment_list = json.loads(file_ids)
            return attachment_list if isinstance(attachment_list, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    @classmethod
    async def add_customer_trace_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddCustomerTraceModel, current_user_id: int
    ) -> CrudResponseModel:
        """
        新增客户跟进记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增客户跟进记录对象
        :param current_user_id: 当前用户 ID
        :return: 新增客户跟进记录校验结果
        """
        # 必填校验
        cls._validate_trace_required_fields(page_object)

        try:
            current_time = int(datetime.now().timestamp())
            add_trace = CustomerTraceModel(
                cid=page_object.cid if page_object.cid is not None else 0,
                contact_id=page_object.contact_id if page_object.contact_id is not None else 0,
                chance_id=page_object.chance_id if page_object.chance_id is not None else 0,
                types=page_object.types if page_object.types is not None else 0,
                stage=page_object.stage if page_object.stage is not None else 0,
                content=page_object.content,
                follow_time=page_object.follow_time if page_object.follow_time is not None else 0,
                next_time=page_object.next_time if page_object.next_time is not None else 0,
                file_ids=page_object.file_ids if page_object.file_ids is not None else '',
                admin_id=current_user_id,
                create_time=current_time,
                update_time=current_time,
                delete_time=0
            )
            await CustomerTraceDao.add_customer_trace_dao(query_db, add_trace)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_customer_trace_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCustomerTraceModel,
            current_user_id: int
    ) -> CrudResponseModel:
        """
        编辑客户跟进记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑客户跟进记录对象
        :param current_user_id: 当前用户 ID
        :return: 编辑客户跟进记录校验结果
        """
        edit_trace = page_object.model_dump(exclude_unset=True, exclude=TRACE_EXTEND_FIELDS)
        trace_info = await cls.customer_trace_detail_services(query_db, page_object.id)

        if trace_info.id:
            # 仅跟进人本人可编辑
            if trace_info.admin_id != current_user_id:
                raise ServiceException(message='仅跟进人本人可编辑该跟进记录')

            # 必填校验
            cls._validate_trace_required_fields(page_object)

            try:
                edit_trace['update_time'] = int(datetime.now().timestamp())
                await CustomerTraceDao.edit_customer_trace_dao(query_db, edit_trace)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='跟进记录不存在')

    @classmethod
    def _validate_trace_required_fields(cls, page_object: AddCustomerTraceModel) -> None:
        """
        跟进记录必填字段校验（联系人、跟进方式、跟进时间、下次沟通时间、跟进内容）

        :param page_object: 新增/编辑客户跟进记录对象
        :return:
        """
        if not page_object.cid:
            raise ServiceException(message='客户 ID 不能为空')
        if not page_object.contact_id:
            raise ServiceException(message='联系人不能为空')
        if not page_object.types:
            raise ServiceException(message='跟进方式不能为空')
        if not page_object.follow_time:
            raise ServiceException(message='跟进时间不能为空')
        if not page_object.next_time:
            raise ServiceException(message='下次沟通时间不能为空')
        if not page_object.content or not page_object.content.strip():
            raise ServiceException(message='跟进内容不能为空')

    @classmethod
    async def delete_customer_trace_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteCustomerTraceModel,
            current_user_id: int
    ) -> CrudResponseModel:
        """
        删除客户跟进记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除客户跟进记录对象
        :param current_user_id: 当前用户 ID
        :return: 删除客户跟进记录校验结果
        """
        if page_object.id:
            try:
                trace = await cls.customer_trace_detail_services(query_db, page_object.id)
                if not trace.id:
                    raise ServiceException(message='跟进记录不存在')

                # 仅跟进人本人可删除
                if trace.admin_id != current_user_id:
                    raise ServiceException(message='仅跟进人本人可删除该跟进记录')

                update_time = int(datetime.now().timestamp())
                await CustomerTraceDao.delete_customer_trace_dao(
                    query_db,
                    CustomerTraceModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入跟进记录 id 为空')

    @classmethod
    async def customer_trace_detail_services(cls, query_db: AsyncSession, trace_id: int) -> CustomerTraceModel:
        """
        获取客户跟进记录详细信息 service

        :param query_db: orm 对象
        :param trace_id: 跟进记录 ID
        :return: 跟进记录 ID 对应的信息
        """
        trace = await CustomerTraceDao.get_customer_trace_detail_by_id(query_db, trace_id)

        if not trace:
            return CustomerTraceModel()

        # 统一转为小驼峰字典后再构建模型，保证与列表/详情接口字段命名一致
        result = CustomerTraceModel(**CamelCaseUtil.transform_result(trace))

        return result

    @classmethod
    async def download_trace_attachment_services(
            cls, request: Request, query_db: AsyncSession, trace_id: int, file_name: str, current_user_id: int
    ) -> FileResponse:
        """
        下载客户跟进记录附件 service
        归属校验：仅跟进记录创建人可下载

        :param request: Request 对象
        :param query_db: orm 对象
        :param trace_id: 跟进记录 ID
        :param file_name: 文件名称
        :param current_user_id: 当前用户 ID
        :return: 文件响应对象
        """
        trace = await CustomerTraceDao.get_customer_trace_detail_by_id(query_db, trace_id)
        if not trace:
            raise ServiceException(message='跟进记录不存在')
        if trace.admin_id != current_user_id:
            raise ServiceException(message='无权下载该跟进记录的附件')

        # 定位目标附件
        attachment_list = cls._parse_attachment_list(trace.file_ids)
        target_attachment = next(
            (item for item in attachment_list if isinstance(item, dict) and item.get('fileName') == file_name), None
        )
        file_path = target_attachment.get('filePath') if target_attachment else None
        if not file_path or '..' in str(file_path) or os.path.isabs(str(file_path)):
            raise ServiceException(message='附件信息无效')

        # 路径穿越防御：解析后必须仍位于附件根目录内
        upload_root = os.path.abspath(UPLOAD_DIR)
        absolute_path = os.path.abspath(os.path.join(upload_root, file_path))
        if not absolute_path.startswith(upload_root):
            raise ServiceException(message='附件信息无效')
        if not os.path.exists(absolute_path):
            raise ServiceException(message='附件文件已被删除')

        file_mime = (target_attachment or {}).get('fileMime') or 'application/octet-stream'
        # 中文文件名 RFC 5987 编码，避免 Content-Disposition 乱码
        encoded_filename = urllib.parse.quote(file_name)
        response = FileResponse(path=absolute_path, media_type=file_mime, filename=file_name)
        response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"

        return response
