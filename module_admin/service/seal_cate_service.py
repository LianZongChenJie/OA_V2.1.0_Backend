from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.seal_cate_dao import SealCateDao
from module_admin.entity.vo.seal_cate_vo import (
    AddSealCateModel,
    DeleteSealCateModel,
    EditSealCateModel,
    SealCateModel,
    SealCatePageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class SealCateService:
    """
    印章类别管理模块服务层
    """

    @classmethod
    async def get_seal_cate_list_services(
            cls, query_db: AsyncSession, query_object: SealCatePageQueryModel, is_page: bool = False
    ) -> dict | list[dict[str, Any]]:
        """
        获取印章类别列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 印章类别列表信息对象
        """
        seal_cate_list_result = await SealCateDao.get_seal_cate_list(query_db, query_object, is_page)

        # 如果是 PageModel 对象，转换为字典
        if isinstance(seal_cate_list_result, PageModel):
            seal_cate_dict = {
                'rows': seal_cate_list_result.rows,
                'pageNum': seal_cate_list_result.page_num,
                'pageSize': seal_cate_list_result.page_size,
                'total': seal_cate_list_result.total,
                'hasNext': seal_cate_list_result.has_next,
            }
        elif isinstance(seal_cate_list_result, dict):
            seal_cate_dict = seal_cate_list_result
        else:
            # 列表类型，直接处理
            from utils.time_format_util import timestamp_to_datetime
            formatted_list = []
            for item in seal_cate_list_result:
                if isinstance(item, dict):
                    formatted_item = cls._format_time_fields(item)
                    camel_item = {
                        'id': formatted_item.get('id'),
                        'title': formatted_item.get('title'),
                        'dids': formatted_item.get('dids'),
                        'keepUid': formatted_item.get('keepUid'),
                        'status': formatted_item.get('status'),
                        'remark': formatted_item.get('remark'),
                        'createTime': formatted_item.get('createTime'),
                        'updateTime': formatted_item.get('updateTime'),
                        'deptNames': formatted_item.get('deptNames'),
                        'keeperName': formatted_item.get('keeperName'),
                    }
                    formatted_list.append(camel_item)
                else:
                    formatted_list.append(item)
            return formatted_list

        # 处理分页数据中的每一行
        from utils.time_format_util import timestamp_to_datetime
        formatted_rows = []
        for row in seal_cate_dict['rows']:
            if isinstance(row, dict):
                formatted_row = cls._format_time_fields(row)
                # 处理部门名称：将数组转换为逗号分隔的字符串
                dept_names = formatted_row.get('deptNames')
                if isinstance(dept_names, list):
                    dept_names_str = ','.join(dept_names) if dept_names else ''
                else:
                    dept_names_str = dept_names or ''
                
                # 只保留驼峰命名字段
                camel_row = {
                    'id': formatted_row.get('id'),
                    'title': formatted_row.get('title'),
                    'dids': formatted_row.get('dids'),
                    'keepUid': formatted_row.get('keepUid'),
                    'status': formatted_row.get('status'),
                    'remark': formatted_row.get('remark'),
                    'createTime': formatted_row.get('createTime'),
                    'updateTime': formatted_row.get('updateTime'),
                    'deptNames': dept_names_str,
                    'keeperName': formatted_row.get('keeperName'),
                }
                formatted_rows.append(camel_row)
        
        # 构建最终返回结果
        result = {
            'rows': formatted_rows,
            'pageNum': seal_cate_dict.get('pageNum'),
            'pageSize': seal_cate_dict.get('pageSize'),
            'total': seal_cate_dict.get('total'),
            'hasNext': seal_cate_dict.get('hasNext'),
        }
        
        return result

    @classmethod
    def _format_time_fields(cls, data: dict) -> dict:
        """
        格式化字典中的时间字段（只保留驼峰命名字段）

        :param data: 原始字典
        :return: 格式化后的字典（只包含驼峰命名）
        """
        from utils.time_format_util import timestamp_to_datetime
        
        # 只提取需要的驼峰命名字段
        formatted = {
            'id': data.get('id'),
            'title': data.get('title'),
            'dids': data.get('dids'),
            'keepUid': data.get('keepUid'),
            'status': data.get('status'),
            'remark': data.get('remark'),
            'deptNames': data.get('deptNames'),
            'keeperName': data.get('keeperName'),
        }
        
        # 需要格式化的时间字段
        time_fields_map = {
            'createTime': ['createTime', 'create_time'],
            'updateTime': ['updateTime', 'update_time'],
        }
        
        for target_field, source_fields in time_fields_map.items():
            for source_field in source_fields:
                if source_field in data and data[source_field] is not None:
                    value = data[source_field]
                    # 如果值为 None、0 或空，设置为空字符串
                    if value is None or value == 0:
                        formatted[target_field] = ''
                    else:
                        # 格式化时间戳为日期时间字符串
                        formatted[target_field] = timestamp_to_datetime(value, '%Y-%m-%d %H:%M:%S')
                    break
            else:
                formatted[target_field] = ''
        
        return formatted

    @classmethod
    async def check_seal_cate_title_unique_services(
            cls, query_db: AsyncSession, page_object: SealCateModel
    ) -> bool:
        """
        校验印章类别名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 印章类别对象
        :return: 校验结果
        """
        seal_cate_id = -1 if page_object.id is None else page_object.id
        seal_cate = await SealCateDao.get_seal_cate_detail_by_info(query_db, page_object)
        if seal_cate and seal_cate.id != seal_cate_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_seal_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddSealCateModel
    ) -> CrudResponseModel:
        """
        新增印章类别信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增印章类别对象
        :return: 新增印章类别校验结果
        """
        if not await cls.check_seal_cate_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增印章类别{page_object.title}失败，印章名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            
            add_data = {
                'title': page_object.title,
                'dids': page_object.dids if page_object.dids is not None else '',
                'keep_uid': page_object.keep_uid if page_object.keep_uid is not None else 0,
                'status': page_object.status if page_object.status is not None else 1,
                'remark': page_object.remark if page_object.remark is not None else '',
                'create_time': current_time,
                'update_time': current_time
            }
            
            logger.info(f'准备插入印章类别数据：{add_data}')
            
            await SealCateDao.add_seal_cate_dao(query_db, add_data)
            await query_db.commit()
            
            logger.info('印章类别新增成功')
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'印章类别新增失败：{str(e)}', exc_info=True)
            raise e

    @classmethod
    async def edit_seal_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditSealCateModel
    ) -> CrudResponseModel:
        """
        编辑印章类别信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑印章类别对象
        :return: 编辑印章类别校验结果
        """
        # 🔥 关键修复：只保留数据库真实存在的字段，排除虚拟字段
        edit_seal_cate = page_object.model_dump(
            exclude_unset=True,
            exclude={"dept_names", "keeper_name", "deptNames", "keeperName"}  # 排除不存在的字段
        )

        seal_cate_info = await cls.seal_cate_detail_services(query_db, page_object.id)

        if seal_cate_info.get('id'):
            if not await cls.check_seal_cate_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改印章类别{page_object.title}失败，印章名称已存在')

            try:
                edit_seal_cate['update_time'] = int(datetime.now().timestamp())
                await SealCateDao.edit_seal_cate_dao(query_db, edit_seal_cate)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='印章类别不存在')

    @classmethod
    async def delete_seal_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteSealCateModel
    ) -> CrudResponseModel:
        """
        删除印章类别信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除印章类别对象
        :return: 删除印章类别校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for seal_cate_id in id_list:
                    seal_cate = await cls.seal_cate_detail_services(query_db, int(seal_cate_id))
                    if not seal_cate.get('id'):
                        raise ServiceException(message='印章类别不存在')

                    update_time = int(datetime.now().timestamp())
                    await SealCateDao.delete_seal_cate_dao(
                        query_db,
                        SealCateModel(id=int(seal_cate_id), update_time=update_time)
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入印章类别 id 为空')

    @classmethod
    async def set_seal_cate_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditSealCateModel
    ) -> CrudResponseModel:
        """
        设置印章类别状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置印章类别状态对象
        :return: 设置印章类别状态校验结果
        """
        seal_cate_info = await cls.seal_cate_detail_services(query_db, page_object.id)

        if seal_cate_info.get('id'):
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await SealCateDao.disable_seal_cate_dao(
                        query_db,
                        SealCateModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await SealCateDao.enable_seal_cate_dao(
                        query_db,
                        SealCateModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='印章类别不存在')

    @classmethod
    async def seal_cate_detail_services(cls, query_db: AsyncSession, seal_cate_id: int) -> dict[str, Any]:
        """
        获取印章类别详细信息 service

        :param query_db: orm 对象
        :param seal_cate_id: 印章类别 id
        :return: 印章类别 id 对应的信息（包含部门名称和保管人姓名）
        """
        seal_cate = await SealCateDao.get_seal_cate_detail_by_id(query_db, seal_cate_id)
        
        if not seal_cate:
            return {}
        
        # 格式化时间字段
        formatted_data = cls._format_time_fields(seal_cate)
        
        # 处理部门名称：将数组转换为逗号分隔的字符串
        dept_names = formatted_data.get('deptNames')
        if isinstance(dept_names, list):
            dept_names_str = ','.join(dept_names) if dept_names else ''
        else:
            dept_names_str = dept_names or ''
        
        # 构建最终返回结果（只包含驼峰命名字段）
        result = {
            'id': formatted_data.get('id'),
            'title': formatted_data.get('title'),
            'dids': formatted_data.get('dids'),
            'keepUid': formatted_data.get('keepUid'),
            'status': formatted_data.get('status'),
            'remark': formatted_data.get('remark'),
            'createTime': formatted_data.get('createTime'),
            'updateTime': formatted_data.get('updateTime'),
            'deptNames': dept_names_str,
            'keeperName': formatted_data.get('keeperName'),
        }

        return result

