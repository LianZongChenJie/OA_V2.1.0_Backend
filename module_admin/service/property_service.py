from datetime import datetime
from typing import Any, Union

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.property_dao import PropertyDao
from module_admin.entity.vo.property_vo import (
    AddPropertyModel,
    DeletePropertyModel,
    EditPropertyModel,
    PropertyModel,
    PropertyPageQueryModel,
)
from utils.camel_converter import ModelConverter
from utils.common_util import CamelCaseUtil
from utils.log_util import logger

class PropertyService:
    """
    资产管理服务层
    """

    @classmethod
    def convert_date_to_timestamp(cls, date_value: Union[int, str, None]) -> int | None:
        """
        将日期值转换为时间戳

        :param date_value: 日期值（可以是时间戳整数或日期字符串）
        :return: 时间戳整数
        """
        if date_value is None:
            return None

        # 如果已经是整数（时间戳），直接返回
        if isinstance(date_value, int):
            return date_value

        # 如果是字符串，尝试转换
        if isinstance(date_value, str):
            try:
                # 尝试解析 YYYY-MM-DD 格式
                return int(datetime.strptime(date_value, '%Y-%m-%d').timestamp())
            except (ValueError, TypeError):
                try:
                    # 尝试解析 YYYY-MM-DD HH:MM:SS 格式
                    return int(datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S').timestamp())
                except (ValueError, TypeError):
                    return None

        return None

    @classmethod
    async def get_property_list_services(
            cls, query_db: AsyncSession, query_object: PropertyPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取资产列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 资产列表信息对象
        """
        property_list_result = await PropertyDao.get_property_list(query_db, query_object, is_page)

        # 如果返回的是分页结果，需要转换 rows 中的数据
        if hasattr(property_list_result, 'rows'):
            transformed_rows = []
            for row in property_list_result.rows:
                # row 是一个元组 (SysProperty, cate_name, brand_name, unit_name, admin_name, update_name)
                if isinstance(row, (list, tuple)):
                    property_obj = row[0]
                    extra_fields = {
                        'cateName': row[1] if len(row) > 1 else None,
                        'brandName': row[2] if len(row) > 2 else None,
                        'unitName': row[3] if len(row) > 3 else None,
                        'adminName': row[4] if len(row) > 4 else None,
                        'updateName': row[5] if len(row) > 5 else None,
                    }

                    # 将 ORM 对象转换为字典（已经是驼峰命名）
                    property_dict = CamelCaseUtil.transform_result(property_obj)
                    # 合并扩展字段（已经是驼峰命名）
                    property_dict.update(extra_fields)
                    # 格式化时间字段
                    property_dict = ModelConverter.time_format(property_dict)
                    transformed_rows.append(property_dict)
                else:
                    transformed_dict = CamelCaseUtil.transform_result(row)
                    transformed_dict = ModelConverter.time_format(transformed_dict)
                    transformed_rows.append(transformed_dict)

            property_list_result.rows = transformed_rows

        return property_list_result

    @classmethod
    async def get_all_property_list_services(cls, query_db: AsyncSession) -> list[dict[str, Any]]:
        """
        获取所有资产列表信息 service

        :param query_db: orm 对象
        :return: 资产列表信息对象
        """
        property_list_result = await PropertyDao.get_all_property_list(query_db)
        transformed_list = CamelCaseUtil.transform_result(property_list_result)

        # 格式化时间字段
        return ModelConverter.list_time_format(transformed_list)

    @classmethod
    async def check_property_title_unique_services(
            cls, query_db: AsyncSession, page_object: PropertyModel
    ) -> bool:
        """
        校验资产名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 资产对象
        :return: 校验结果
        """
        property_id = -1 if page_object.id is None else page_object.id
        property = await PropertyDao.get_property_detail_by_info(query_db, page_object)
        if property and property.id != property_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_property_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddPropertyModel
    ) -> CrudResponseModel:
        """
        新增资产信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增资产对象
        :return: 新增资产校验结果
        """
        if not await cls.check_property_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增资产{page_object.title}失败，资产名称已存在')

        try:
            current_time = int(datetime.now().timestamp())

            # 转换日期字段为时间戳
            quality_time = cls.convert_date_to_timestamp(page_object.quality_time)
            buy_time = cls.convert_date_to_timestamp(page_object.buy_time)

            # 直接使用原始请求数据
            body = await request.json()

            # 构建数据字典 - 注意前端发送的是驼峰命名
            add_dict = {
                'title': body.get('title'),
                'code': body.get('code', ''),
                'thumb': int(body.get('thumb', 0) or 0),
                'cate_id': int(body.get('cateId', 0) or 0),
                'brand_id': int(body.get('brandId', 0) or 0),
                'unit_id': int(body.get('unitId', 0) or 0),
                'quality_time': quality_time if quality_time is not None else 0,
                'buy_time': buy_time if buy_time is not None else 0,
                'price': float(body.get('price', 0) or 0),
                'rate': float(body.get('rate', 0) or 0),
                'model_': body.get('model', ''),
                'address': body.get('address', ''),
                'user_dids': str(body.get('userDids', '') or ''),
                'user_ids': str(body.get('userIds', '') or ''),
                'content': body.get('content', ''),
                'file_ids': body.get('fileIds', ''),
                'source': int(body.get('source', 1) or 1),
                'purchase_id': int(body.get('purchaseId', 0) or 0),
                'status': int(body.get('status', 1) or 1),
                'admin_id': int(page_object.admin_id) if page_object.admin_id else 0,
                'create_time': current_time,
                'update_time': current_time,
            }

            logger.info(f'Service 层 - 传递给 DAO 的数据: {add_dict}')

            # 直接调用 DAO 层，传入字典而不是 PropertyModel 对象
            await PropertyDao.add_property_dao_from_dict(query_db, add_dict)
            await query_db.commit()
            logger.info(f'========== 新增资产成功 ==========')
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'新增资产失败: {str(e)}')
            import traceback
            logger.error(traceback.format_exc())
            raise e

    @classmethod
    async def edit_property_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPropertyModel
    ) -> CrudResponseModel:
        """
        编辑资产信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑资产对象
        :return: 编辑资产校验结果
        """
        edit_property = page_object.model_dump(exclude_unset=True)
        property_info = await cls.property_detail_services(query_db, page_object.id)

        if property_info.id:
            if not await cls.check_property_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改资产{page_object.title}失败，资产名称已存在')

            try:
                # 转换日期字段为时间戳
                if 'quality_time' in edit_property:
                    edit_property['quality_time'] = cls.convert_date_to_timestamp(edit_property['quality_time'])

                if 'buy_time' in edit_property:
                    edit_property['buy_time'] = cls.convert_date_to_timestamp(edit_property['buy_time'])

                edit_property['update_time'] = int(datetime.now().timestamp())

                # 确保 update_id 被设置
                if page_object.update_id is not None:
                    edit_property['update_id'] = page_object.update_id

                await PropertyDao.edit_property_dao(query_db, edit_property)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='资产不存在')

    @classmethod
    async def delete_property_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeletePropertyModel
    ) -> CrudResponseModel:
        """
        删除资产信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除资产对象
        :return: 删除资产校验结果
        """
        if page_object.id:
            try:
                property = await cls.property_detail_services(query_db, page_object.id)
                if not property.id:
                    raise ServiceException(message='资产不存在')

                update_time = int(datetime.now().timestamp())
                await PropertyDao.delete_property_dao(
                    query_db,
                    PropertyModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入资产 id 为空')

    @classmethod
    async def set_property_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPropertyModel
    ) -> CrudResponseModel:
        """
        设置资产状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置资产状态对象
        :return: 设置资产状态校验结果
        """
        property_info = await cls.property_detail_services(query_db, page_object.id)

        if property_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                # 直接使用通用更新方法，支持所有状态值
                await PropertyDao.edit_property_dao(
                    query_db,
                    {'id': page_object.id, 'status': page_object.status, 'update_time': update_time}
                )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='资产不存在')

    @classmethod
    async def property_detail_services(cls, query_db: AsyncSession, property_id: int) -> PropertyModel:
        """
        获取资产详细信息 service

        :param query_db: orm 对象
        :param property_id: 资产 ID
        :return: 资产 ID 对应的信息
        """
        from module_admin.entity.do.property_do import OaProperty
        from module_admin.entity.do.property_cate_do import SysPropertyCate
        from module_admin.entity.do.property_brand_do import SysPropertyBrand
        from module_admin.entity.do.property_unit_do import SysPropertyUnit
        from module_admin.entity.do.user_do import SysUser
        from sqlalchemy import alias
        
        property = await PropertyDao.get_property_detail_by_id(query_db, property_id)
        
        if not property:
            raise ServiceException(message=f'资产 ID {property_id} 不存在')
        
        # 连表查询获取关联字段
        UpdateUser = alias(SysUser.__table__, 'update_user')
        
        query = (
            select(
                OaProperty,
                SysPropertyCate.title.label('cate_name'),
                SysPropertyBrand.title.label('brand_name'),
                SysPropertyUnit.title.label('unit_name'),
                SysUser.nick_name.label('admin_name'),
                UpdateUser.c.nick_name.label('update_name')
            )
            .outerjoin(SysPropertyCate, OaProperty.cate_id == SysPropertyCate.id)
            .outerjoin(SysPropertyBrand, OaProperty.brand_id == SysPropertyBrand.id)
            .outerjoin(SysPropertyUnit, OaProperty.unit_id == SysPropertyUnit.id)
            .outerjoin(SysUser, OaProperty.admin_id == SysUser.user_id)
            .outerjoin(UpdateUser, OaProperty.update_id == UpdateUser.c.user_id)
            .where(OaProperty.id == property_id)
        )
        
        result = (await query_db.execute(query)).first()
        
        if result:
            property_obj = result[0]
            extra_fields = {
                'cateName': result[1] if len(result) > 1 else None,
                'brandName': result[2] if len(result) > 2 else None,
                'unitName': result[3] if len(result) > 3 else None,
                'adminName': result[4] if len(result) > 4 else None,
                'updateName': result[5] if len(result) > 5 else None,
            }
            
            # 将 ORM 对象转换为字典
            property_dict = CamelCaseUtil.transform_result(property_obj)
            # 合并扩展字段
            property_dict.update(extra_fields)
            # 格式化时间字段
            property_dict = ModelConverter.time_format(property_dict)
            
            return PropertyModel(**property_dict)
        else:
            raise ServiceException(message=f'资产 ID {property_id} 不存在')
