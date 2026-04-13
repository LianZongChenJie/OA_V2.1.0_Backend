from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_administrative.dao.overtimes_dao import OvertimesDao
from module_administrative.entity.vo.overtimes_vo import (
    AddOvertimesModel,
    DeleteOvertimesModel,
    EditOvertimesModel,
    OvertimesModel,
    OvertimesPageQueryModel,
)
from utils.camel_converter import ModelConverter
from utils.common_util import CamelCaseUtil


class OvertimesService:
    """
    加班记录管理服务层
    """

    @classmethod
    async def get_overtimes_list_services(
            cls, query_db: AsyncSession, query_object: OvertimesPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取加班记录列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 加班记录列表信息对象
        """
        overtimes_list_result = await OvertimesDao.get_overtimes_list(query_db, query_object, is_page)

        # 如果返回的是分页结果，需要转换 rows 中的数据
        if hasattr(overtimes_list_result, 'rows'):
            transformed_rows = []
            for row in overtimes_list_result.rows:
                transformed_dict = CamelCaseUtil.transform_result(row)
                transformed_rows.append(transformed_dict)

            overtimes_list_result.rows = transformed_rows

        return overtimes_list_result

    @classmethod
    async def add_overtimes_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddOvertimesModel, user_id: int, dept_id: int
    ) -> CrudResponseModel:
        """
        新增加班记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增加班记录对象
        :param user_id: 用户ID
        :param dept_id: 部门ID
        :return: 新增加班记录校验结果
        """
        try:
            current_time = int(datetime.now().timestamp())
            overtimes_data = page_object.model_dump(exclude_unset=True)

            # 验证结束时间不能小于开始时间
            if 'start_date' in overtimes_data and 'end_date' in overtimes_data:
                if overtimes_data['end_date'] < overtimes_data['start_date']:
                    raise ServiceException(message='结束时间不能小于开始时间')

            overtimes_data['create_time'] = current_time
            overtimes_data['update_time'] = current_time
            overtimes_data['delete_time'] = 0
            overtimes_data['admin_id'] = user_id
            overtimes_data['did'] = dept_id

            await OvertimesDao.add_overtimes_dao(query_db, overtimes_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_overtimes_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditOvertimesModel
    ) -> CrudResponseModel:
        """
        编辑加班记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑加班记录对象
        :return: 编辑加班记录校验结果
        """
        overtimes_data = page_object.model_dump(exclude_unset=True)
        overtimes_info = await cls.overtimes_detail_services(query_db, page_object.id)

        if overtimes_info.id:
            try:
                # 验证结束时间不能小于开始时间
                if 'start_date' in overtimes_data and 'end_date' in overtimes_data:
                    if overtimes_data['end_date'] < overtimes_data['start_date']:
                        raise ServiceException(message='结束时间不能小于开始时间')

                overtimes_data['update_time'] = int(datetime.now().timestamp())

                await OvertimesDao.edit_overtimes_dao(query_db, overtimes_data)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='加班记录不存在')

    @classmethod
    async def delete_overtimes_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteOvertimesModel
    ) -> CrudResponseModel:
        """
        删除加班记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除加班记录对象
        :return: 删除加班记录校验结果
        """
        if page_object.id:
            try:
                overtimes = await cls.overtimes_detail_services(query_db, page_object.id)
                if not overtimes.id:
                    raise ServiceException(message='加班记录不存在')

                await OvertimesDao.delete_overtimes_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入加班记录 id 为空')

    @classmethod
    async def overtimes_detail_services(cls, query_db: AsyncSession, overtimes_id: int) -> OvertimesModel:
        """
        获取加班记录详细信息 service

        :param query_db: orm 对象
        :param overtimes_id: 加班记录 ID
        :return: 加班记录 ID 对应的信息
        """
        result = await OvertimesDao.get_overtimes_detail_by_id(query_db, overtimes_id)

        if result:
            overtimes_dict = CamelCaseUtil.transform_result(result)
            return OvertimesModel(**overtimes_dict)
        else:
            raise ServiceException(message=f'加班记录 ID {overtimes_id} 不存在')