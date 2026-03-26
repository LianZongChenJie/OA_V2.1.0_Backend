from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.official_docs_dao import OfficialDocsDao
from module_admin.entity.vo.official_docs_vo import (
    AddOfficialDocsModel,
    DeleteOfficialDocsModel,
    EditOfficialDocsModel,
    OfficialDocsModel,
    OfficialDocsPageQueryModel,
    PendingOfficialDocsModel,
    ReviewedOfficialDocsModel,
)
from utils.common_util import CamelCaseUtil
from utils.time_format_util import TimeFormatUtil


class OfficialDocsService:
    """
    公文管理模块服务层
    """

    @classmethod
    async def check_official_title_unique_services(
            cls, query_db: AsyncSession, page_object: OfficialDocsModel
    ) -> bool:
        """
        校验公文主题是否唯一 service

        :param query_db: orm 对象
        :param page_object: 公文对象
        :return: 校验结果
        """
        official_id = -1 if page_object.id is None else page_object.id
        official = await OfficialDocsDao.get_official_docs_detail_by_info(query_db, page_object)
        if official and official.id != official_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def check_official_code_unique_services(
            cls, query_db: AsyncSession, page_object: OfficialDocsModel
    ) -> bool:
        """
        校验公文编号是否唯一 service

        :param query_db: orm 对象
        :param page_object: 公文对象
        :return: 校验结果
        """
        official_id = -1 if page_object.id is None else page_object.id
        if page_object.code:
            official = await OfficialDocsDao.get_official_docs_detail_by_info(
                query_db, 
                OfficialDocsModel(code=page_object.code)
            )
            if official and official.id != official_id:
                return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def get_official_docs_list_services(
            cls, query_db: AsyncSession, query_object: OfficialDocsPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取公文列表信息 service

        :param query_db: orm 对象
        :param query_object: 分页查询参数对象
        :param is_page: 是否开启分页
        :return: 公文列表信息对象
        """
        docs_list_result = await OfficialDocsDao.get_official_docs_list(query_db, query_object, is_page)

        return CamelCaseUtil.transform_result(docs_list_result)

    @classmethod
    async def get_pending_docs_list_services(
            cls, query_db: AsyncSession, query_object: PendingOfficialDocsModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取待审公文列表 service

        :param query_db: orm 对象
        :param query_object: 分页查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 待审公文列表信息对象
        """
        docs_list_result = await OfficialDocsDao.get_pending_docs_list(query_db, query_object, user_id, is_page)

        return CamelCaseUtil.transform_result(docs_list_result)

    @classmethod
    async def get_reviewed_docs_list_services(
            cls, query_db: AsyncSession, query_object: ReviewedOfficialDocsModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取已审公文列表 service

        :param query_db: orm 对象
        :param query_object: 分页查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 已审公文列表信息对象
        """
        docs_list_result = await OfficialDocsDao.get_reviewed_docs_list(query_db, query_object, user_id, is_page)

        return CamelCaseUtil.transform_result(docs_list_result)

    @classmethod
    async def add_official_docs_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddOfficialDocsModel, user_id: int
    ) -> CrudResponseModel:
        """
        新增公文信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增公文对象
        :param user_id: 当前用户 ID
        :return: 新增公文校验结果
        """
        # 校验公文主题是否唯一
        if not await cls.check_official_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增公文失败，公文主题已存在')
        
        # 校验公文编号是否唯一
        if not await cls.check_official_code_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增公文失败，公文编号已存在')
        
        try:
            current_time = int(datetime.now().timestamp())
            # 只获取数据库表中存在的字段，排除扩展字段
            docs_data = page_object.model_dump(
                exclude_unset=True,
                exclude={
                    'id', 'secrets_str', 'urgency_str', 'check_status_str',
                    'draft_name', 'draft_dname', 'send_names', 'copy_names',
                    'share_names', 'file_array', 'create_time', 'update_time',
                    'delete_time'
                }
            )
            docs_data['admin_id'] = user_id
            docs_data['create_time'] = current_time
            docs_data['update_time'] = current_time
            docs_data['delete_time'] = 0

            await OfficialDocsDao.add_official_docs_dao(query_db, OfficialDocsModel(**docs_data))
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_official_docs_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditOfficialDocsModel
    ) -> CrudResponseModel:
        """
        编辑公文信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑公文对象
        :return: 编辑公文校验结果
        """
        if page_object.id:
            try:
                # 只获取数据库表中存在的字段，排除扩展字段和主键
                edit_docs = page_object.model_dump(
                    exclude_unset=True,
                    exclude={
                        'id', 'secrets_str', 'urgency_str', 'check_status_str',
                        'draft_name', 'draft_dname', 'send_names', 'copy_names',
                        'share_names', 'file_array', 'create_time', 'delete_time'
                    }
                )
                edit_docs['update_time'] = int(datetime.now().timestamp())
                await OfficialDocsDao.edit_official_docs_dao(query_db, page_object.id, edit_docs)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='公文不存在')

    @classmethod
    async def delete_official_docs_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteOfficialDocsModel
    ) -> CrudResponseModel:
        """
        删除公文信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除公文对象
        :return: 删除公文校验结果
        """
        if page_object.id:
            try:
                docs = await cls.official_docs_detail_services(query_db, page_object.id)
                if not docs.id:
                    raise ServiceException(message='公文不存在')

                update_time = int(datetime.now().timestamp())
                await OfficialDocsDao.delete_official_docs_dao(
                    query_db,
                    OfficialDocsModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入公文 id 为空')

    @classmethod
    async def official_docs_detail_services(cls, query_db: AsyncSession, docs_id: int) -> OfficialDocsModel:
        """
        获取公文详细信息 service

        :param query_db: orm 对象
        :param docs_id: 公文 id
        :return: 公文 id 对应的信息
        """
        docs_detail = await OfficialDocsDao.get_official_docs_detail_by_id(query_db, docs_id)

        if not docs_detail:
            return OfficialDocsModel()

        docs_info = docs_detail.get('docs_info')
        result_dict = CamelCaseUtil.transform_result(docs_info)

        result_dict['draft_name'] = docs_detail.get('draft_name')
        result_dict['draft_dname'] = docs_detail.get('draft_dname')
        result_dict['send_names'] = ','.join(docs_detail.get('send_names', []))
        result_dict['copy_names'] = ','.join(docs_detail.get('copy_names', []))
        result_dict['share_names'] = ','.join(docs_detail.get('share_names', []))
        result_dict['file_array'] = docs_detail.get('file_array', [])

        result = OfficialDocsModel(**result_dict)

        return result
