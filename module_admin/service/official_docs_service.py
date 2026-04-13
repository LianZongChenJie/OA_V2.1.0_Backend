from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.official_docs_dao import OfficialDocsDao
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.do.dept_do import SysDept
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
    async def _format_docs_list(cls, docs_list: list[dict[str, Any]], query_db: AsyncSession) -> list[dict[str, Any]]:
        """
        格式化公文列表数据
        
        :param docs_list: 公文列表（已经是驼峰命名的字典）
        :param query_db: 数据库会话
        :return: 格式化后的列表
        """
        if not docs_list:
            return docs_list
        
        secrets_map = {1: '公开', 2: '秘密', 3: '机密'}
        urgency_map = {1: '普通', 2: '紧急', 3: '加急'}
        
        for item in docs_list:
            if not isinstance(item, dict):
                continue
            
            secrets_val = item.get('secrets')
            if secrets_val:
                item['secretsStr'] = secrets_map.get(secrets_val, '')
            else:
                item['secretsStr'] = ''
            
            urgency_val = item.get('urgency')
            if urgency_val:
                item['urgencyStr'] = urgency_map.get(urgency_val, '')
            else:
                item['urgencyStr'] = ''
            
            create_time = item.get('createTime')
            if create_time and isinstance(create_time, (int, float)) and create_time > 0:
                try:
                    if create_time > 1e12:
                        create_time_seconds = create_time / 1000
                    else:
                        create_time_seconds = create_time
                    item['createTime'] = datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    logger.error(f"创建时间格式化失败: {create_time}, 错误: {e}")
                    item['createTime'] = ''
            else:
                item['createTime'] = ''
            
            draft_time = item.get('draftTime')
            if draft_time and isinstance(draft_time, (int, float)) and draft_time > 0:
                try:
                    if draft_time > 1e12:
                        draft_time_seconds = draft_time / 1000
                    else:
                        draft_time_seconds = draft_time
                    item['draftTime'] = datetime.fromtimestamp(draft_time_seconds).strftime('%Y-%m-%d')
                except Exception as e:
                    logger.error(f"拟稿日期格式化失败: {draft_time}, 错误: {e}")
                    item['draftTime'] = ''
            else:
                item['draftTime'] = ''
            
            update_time = item.get('updateTime')
            if update_time and isinstance(update_time, (int, float)) and update_time > 0:
                try:
                    if update_time > 1e12:
                        update_time_seconds = update_time / 1000
                    else:
                        update_time_seconds = update_time
                    item['updateTime'] = datetime.fromtimestamp(update_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    logger.error(f"更新时间格式化失败: {update_time}, 错误: {e}")
                    item['updateTime'] = ''
            else:
                item['updateTime'] = ''
            
            check_time = item.get('checkTime')
            if check_time and isinstance(check_time, (int, float)) and check_time > 0:
                try:
                    if check_time > 1e12:
                        check_time_seconds = check_time / 1000
                    else:
                        check_time_seconds = check_time
                    item['checkTime'] = datetime.fromtimestamp(check_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    logger.error(f"审核时间格式化失败: {check_time}, 错误: {e}")
                    item['checkTime'] = ''
            else:
                item['checkTime'] = ''
            
            draft_uid = item.get('draftUid')
            if draft_uid and isinstance(draft_uid, int) and draft_uid > 0:
                try:
                    draft_user = await query_db.execute(
                        select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id == draft_uid)
                    )
                    user_info = draft_user.first()
                    if user_info:
                        item['draftName'] = user_info.nick_name or user_info.user_name
                    else:
                        item['draftName'] = ''
                except Exception as e:
                    logger.error(f"查询拟稿人失败: {e}")
                    item['draftName'] = ''
            else:
                item['draftName'] = ''
            
            did = item.get('did')
            if did and isinstance(did, int) and did > 0:
                try:
                    dept = await query_db.execute(
                        select(SysDept.dept_name).where(SysDept.dept_id == did)
                    )
                    dept_info = dept.scalar_one_or_none()
                    item['draftDname'] = dept_info if dept_info else ''
                except Exception as e:
                    logger.error(f"查询拟稿部门失败: {e}")
                    item['draftDname'] = ''
            else:
                item['draftDname'] = ''
        
        return docs_list

    @classmethod
    async def get_official_docs_list_services(
            cls, query_db: AsyncSession, query_object: OfficialDocsPageQueryModel, is_page: bool = False, user_id: int = 0
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取公文列表信息 service

        :param query_db: orm 对象
        :param query_object: 分页查询参数对象
        :param is_page: 是否开启分页
        :param user_id: 当前用户 ID（用于 tab 筛选）
        :return: 公文列表信息对象
        """
        if hasattr(query_object, '_user_id'):
            query_object._user_id = user_id
        else:
            setattr(query_object, '_user_id', user_id)
        
        docs_list_result = await OfficialDocsDao.get_official_docs_list(query_db, query_object, is_page)

        docs_list_result = CamelCaseUtil.transform_result(docs_list_result)

        if is_page and hasattr(docs_list_result, 'rows') and docs_list_result.rows:
            formatted_rows = await cls._format_docs_list(docs_list_result.rows, query_db)
            docs_list_result.rows = formatted_rows
        elif not is_page and docs_list_result:
            docs_list_result = await cls._format_docs_list(docs_list_result, query_db)

        return docs_list_result

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
            
            # 将时间字符串转换回时间戳
            if 'draft_time' in docs_data and isinstance(docs_data['draft_time'], str):
                try:
                    dt = datetime.fromisoformat(docs_data['draft_time'])
                    docs_data['draft_time'] = int(dt.timestamp())
                except ValueError:
                    pass
            
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
                
                # 将时间字符串转换回时间戳
                if 'draft_time' in edit_docs and isinstance(edit_docs['draft_time'], str):
                    try:
                        dt = datetime.fromisoformat(edit_docs['draft_time'])
                        edit_docs['draft_time'] = int(dt.timestamp())
                    except ValueError:
                        pass
                
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

        result_dict['draftName'] = docs_detail.get('draft_name', '')
        result_dict['draftDname'] = docs_detail.get('draft_dname', '')
        result_dict['sendNames'] = ','.join(docs_detail.get('send_names', []))
        result_dict['copyNames'] = ','.join(docs_detail.get('copy_names', []))
        result_dict['shareNames'] = ','.join(docs_detail.get('share_names', []))
        result_dict['fileArray'] = docs_detail.get('file_array', [])

        draft_time = result_dict.get('draftTime')
        if draft_time and isinstance(draft_time, (int, float)) and draft_time > 0:
            try:
                if draft_time > 1e12:
                    draft_time_seconds = draft_time / 1000
                else:
                    draft_time_seconds = draft_time
                result_dict['draftTime'] = datetime.fromtimestamp(draft_time_seconds).strftime('%Y-%m-%d')
            except Exception as e:
                logger.error(f"拟稿日期格式化失败: {draft_time}, 错误: {e}")
                result_dict['draftTime'] = ''
        else:
            result_dict['draftTime'] = ''

        create_time = result_dict.get('createTime')
        if create_time and isinstance(create_time, (int, float)) and create_time > 0:
            try:
                if create_time > 1e12:
                    create_time_seconds = create_time / 1000
                else:
                    create_time_seconds = create_time
                result_dict['createTime'] = datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.error(f"创建时间格式化失败: {create_time}, 错误: {e}")
                result_dict['createTime'] = ''
        else:
            result_dict['createTime'] = ''

        update_time = result_dict.get('updateTime')
        if update_time and isinstance(update_time, (int, float)) and update_time > 0:
            try:
                if update_time > 1e12:
                    update_time_seconds = update_time / 1000
                else:
                    update_time_seconds = update_time
                result_dict['updateTime'] = datetime.fromtimestamp(update_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.error(f"更新时间格式化失败: {update_time}, 错误: {e}")
                result_dict['updateTime'] = ''
        else:
            result_dict['updateTime'] = ''

        check_time = result_dict.get('checkTime')
        if check_time and isinstance(check_time, (int, float)) and check_time > 0:
            try:
                if check_time > 1e12:
                    check_time_seconds = check_time / 1000
                else:
                    check_time_seconds = check_time
                result_dict['checkTime'] = datetime.fromtimestamp(check_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.error(f"审核时间格式化失败: {check_time}, 错误: {e}")
                result_dict['checkTime'] = ''
        else:
            result_dict['checkTime'] = ''

        result = OfficialDocsModel(**result_dict)

        return result
