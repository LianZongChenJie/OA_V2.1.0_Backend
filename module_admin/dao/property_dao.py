from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update, alias
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.property_do import OaProperty as SysProperty
from module_admin.entity.do.property_cate_do import SysPropertyCate
from module_admin.entity.do.property_brand_do import SysPropertyBrand
from module_admin.entity.do.property_unit_do import SysPropertyUnit
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.vo.property_vo import PropertyModel, PropertyPageQueryModel
from utils.page_util import PageUtil
from utils.log_util import logger

class PropertyDao:
    """
    资产管理模块数据库操作层
    """

    @classmethod
    async def get_property_detail_by_id(cls, db: AsyncSession, property_id: int) -> SysProperty | None:
        """
        根据资产 ID 获取资产详细信息

        :param db: orm 对象
        :param property_id: 资产 ID
        :return: 资产信息对象
        """
        property_info = (
            (await db.execute(select(SysProperty).where(SysProperty.id == property_id)))
            .scalars()
            .first()
        )

        return property_info

    @classmethod
    async def get_property_detail_by_info(cls, db: AsyncSession, property: PropertyModel) -> SysProperty | None:
        """
        根据资产参数获取信息

        :param db: orm 对象
        :param property: 资产参数对象
        :return: 资产信息对象
        """
        query_conditions = []
        if property.title:
            query_conditions.append(SysProperty.title == property.title)

        if query_conditions:
            property_info = (
                (await db.execute(select(SysProperty).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            property_info = None

        return property_info

    @classmethod
    async def get_property_list(
            cls, db: AsyncSession, query_object: PropertyPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取资产列表信息（包含关联字段）

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 资产列表信息对象
        """
        # 创建用户表的别名，用于查询更新人
        UpdateUser = alias(SysUser.__table__, 'update_user')
        
        # 构建查询条件列表
        conditions = [
            SysProperty.status != -1,
        ]
        
        # 添加动态查询条件
        if query_object.title:
            conditions.append(SysProperty.title.like(f'%{query_object.title}%'))
        
        if query_object.code:
            conditions.append(SysProperty.code.like(f'%{query_object.code}%'))
        
        if query_object.cate_id is not None:
            conditions.append(SysProperty.cate_id == query_object.cate_id)
        
        if query_object.brand_id is not None:
            conditions.append(SysProperty.brand_id == query_object.brand_id)
        
        if query_object.unit_id is not None:
            conditions.append(SysProperty.unit_id == query_object.unit_id)
        
        if query_object.status is not None:
            conditions.append(SysProperty.status == query_object.status)
        
        if query_object.source is not None:
            conditions.append(SysProperty.source == query_object.source)
        
        # 构建联合查询，关联分类、品牌、单位和用户表
        query = (
            select(
                SysProperty,
                SysPropertyCate.title.label('cate_name'),
                SysPropertyBrand.title.label('brand_name'),
                SysPropertyUnit.title.label('unit_name'),
                SysUser.nick_name.label('admin_name'),
                UpdateUser.c.nick_name.label('update_name')
            )
            .outerjoin(SysPropertyCate, SysProperty.cate_id == SysPropertyCate.id)
            .outerjoin(SysPropertyBrand, SysProperty.brand_id == SysPropertyBrand.id)
            .outerjoin(SysPropertyUnit, SysProperty.unit_id == SysPropertyUnit.id)
            .outerjoin(SysUser, SysProperty.admin_id == SysUser.user_id)
            .outerjoin(UpdateUser, SysProperty.update_id == UpdateUser.c.user_id)
            .where(*conditions)
            .order_by(SysProperty.create_time.desc())
            .distinct()
        )
        
        property_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return property_list

    @classmethod
    async def get_all_property_list(cls, db: AsyncSession) -> list[dict]:
        """
        获取所有资产列表信息

        :param db: orm 对象
        :return: 资产列表信息对象
        """
        query = (
            select(SysProperty)
            .where(SysProperty.status != -1)
            .order_by(SysProperty.create_time.desc())
            .distinct()
        )
        result = (await db.execute(query)).scalars().all()

        return [item.__dict__ for item in result if not item._sa_instance_state.deleted]

    @classmethod
    async def add_property_dao(cls, db: AsyncSession, property: PropertyModel) -> SysProperty:
        """
        新增资产数据库操作

        :param db: orm 对象
        :param property: 资产对象
        :return:
        """
        # 获取所有字段数据，包括 None 值
        property_data = property.model_dump(by_alias=False, exclude_none=False)
        
        logger.info(f'DAO 层接收到的原始数据: {property_data}')
        
        # 移除扩展字段（这些字段不在数据库表中）
        extension_fields = ['cate_name', 'brand_name', 'unit_name', 'admin_name', 'update_name']
        for field in extension_fields:
            property_data.pop(field, None)
        
        # Pydantic 使用 model_ 避免与保留字冲突，需要转换为数据库字段 model
        if 'model_' in property_data:
            property_data['model'] = property_data.pop('model_')
        
        # 处理 None 值，设置默认值
        property_data['thumb'] = property_data.get('thumb') if property_data.get('thumb') is not None else 0
        property_data['cate_id'] = property_data.get('cate_id') if property_data.get('cate_id') is not None else 0
        property_data['brand_id'] = property_data.get('brand_id') if property_data.get('brand_id') is not None else 0
        property_data['unit_id'] = property_data.get('unit_id') if property_data.get('unit_id') is not None else 0
        property_data['quality_time'] = property_data.get('quality_time') if property_data.get('quality_time') is not None else 0
        property_data['buy_time'] = property_data.get('buy_time') if property_data.get('buy_time') is not None else 0
        property_data['price'] = property_data.get('price') if property_data.get('price') is not None else 0
        property_data['rate'] = property_data.get('rate') if property_data.get('rate') is not None else 0
        property_data['model'] = property_data.get('model') if property_data.get('model') is not None else ''
        property_data['address'] = property_data.get('address') if property_data.get('address') is not None else ''
        property_data['user_dids'] = property_data.get('user_dids') if property_data.get('user_dids') is not None else ''
        property_data['user_ids'] = property_data.get('user_ids') if property_data.get('user_ids') is not None else ''
        property_data['content'] = property_data.get('content') if property_data.get('content') is not None else ''
        property_data['file_ids'] = property_data.get('file_ids') if property_data.get('file_ids') is not None else ''
        property_data['source'] = property_data.get('source') if property_data.get('source') is not None else 1
        property_data['purchase_id'] = property_data.get('purchase_id') if property_data.get('purchase_id') is not None else 0
        property_data['status'] = property_data.get('status') if property_data.get('status') is not None else 1
        property_data['admin_id'] = property_data.get('admin_id') if property_data.get('admin_id') is not None else 0
        property_data['create_time'] = property_data.get('create_time') if property_data.get('create_time') is not None else 0
        property_data['update_id'] = property_data.get('update_id') if property_data.get('update_id') is not None else 0
        property_data['update_time'] = property_data.get('update_time') if property_data.get('update_time') is not None else 0
        
        logger.info(f'DAO 层处理后的数据: {property_data}')
        
        db_property = SysProperty(**property_data)
        db.add(db_property)
        await db.flush()

        return db_property

    @classmethod
    async def add_property_dao_from_dict(cls, db: AsyncSession, property_dict: dict) -> SysProperty:
        """
        从字典新增资产数据库操作

        :param db: orm 对象
        :param property_dict: 资产数据字典
        :return:
        """
        logger.info(f'DAO 层接收到的字典数据: {property_dict}')
        
        # Pydantic 使用 model_ 避免与保留字冲突，需要转换为数据库字段 model
        if 'model_' in property_dict:
            property_dict['model'] = property_dict.pop('model_')
        
        logger.info(f'DAO 层处理后的字典数据: {property_dict}')
        
        db_property = SysProperty(**property_dict)
        db.add(db_property)
        await db.flush()

        return db_property

    @classmethod
    async def edit_property_dao(cls, db: AsyncSession, property: dict) -> None:
        """
        编辑资产数据库操作

        :param db: orm 对象
        :param property: 需要更新的资产字典
        :return:
        """
        await db.execute(update(SysProperty), [property])

    @classmethod
    async def delete_property_dao(cls, db: AsyncSession, property: PropertyModel) -> None:
        """
        删除资产数据库操作（逻辑删除）

        :param db: orm 对象
        :param property: 资产对象
        :return:
        """
        update_time = property.update_time if property.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysProperty)
            .where(SysProperty.id == property.id)
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_property_dao(cls, db: AsyncSession, property: PropertyModel) -> None:
        """
        禁用资产数据库操作

        :param db: orm 对象
        :param property: 资产对象
        :return:
        """
        update_time = property.update_time if property.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysProperty)
            .where(SysProperty.id == property.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_property_dao(cls, db: AsyncSession, property: PropertyModel) -> None:
        """
        启用资产数据库操作

        :param db: orm 对象
        :param property: 资产对象
        :return:
        """
        update_time = property.update_time if property.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysProperty)
            .where(SysProperty.id == property.id)
            .values(status=1, update_time=update_time)
        )