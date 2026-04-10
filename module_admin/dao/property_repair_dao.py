from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.property_repair_do import OaPropertyRepair
from module_admin.entity.vo.property_repair_vo import PropertyRepairPageQueryModel
from utils.page_util import PageUtil

class PropertyRepairDao:
    """
    資產維修記錄管理模塊數據庫操作層
    """

    @classmethod
    async def get_property_repair_detail_by_id(cls, db: AsyncSession, repair_id: int) -> OaPropertyRepair | None:
        """
        根據維修記錄 ID 獲取維修記錄詳細信息

        :param db: orm 對象
        :param repair_id: 維修記錄 ID
        :return: 維修記錄信息對象
        """
        repair_info = (
            (await db.execute(select(OaPropertyRepair).where(OaPropertyRepair.id == repair_id)))
            .scalars()
            .first()
        )

        return repair_info

    @classmethod
    async def get_property_repair_list(
            cls, db: AsyncSession, query_object: PropertyRepairPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取维修记录列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 维修记录列表信息对象
        """
        # 使用关联查询获取资产名称、分类、品牌和跟进人姓名
        from module_admin.entity.do.property_do import OaProperty
        from module_admin.entity.do.property_cate_do import SysPropertyCate
        from module_admin.entity.do.property_brand_do import SysPropertyBrand
        from module_admin.entity.do.user_do import SysUser
        
        query = (
            select(
                OaPropertyRepair,
                OaProperty.title.label('property_name'),
                SysPropertyCate.title.label('cate_name'),
                SysPropertyBrand.title.label('brand_name'),
                SysUser.nick_name.label('director_name')
            )
            .join(OaProperty, OaProperty.id == OaPropertyRepair.property_id, isouter=True)
            .join(SysPropertyCate, SysPropertyCate.id == OaProperty.cate_id, isouter=True)
            .join(SysPropertyBrand, SysPropertyBrand.id == OaProperty.brand_id, isouter=True)
            .join(SysUser, SysUser.user_id == OaPropertyRepair.director_id, isouter=True)
            .where(OaPropertyRepair.delete_time == 0)
        )
        
        # 关键词搜索（搜索资产名称或维修原因）
        if query_object.keywords:
            query = query.where(
                or_(
                    OaProperty.title.like(f'%{query_object.keywords}%'),
                    OaPropertyRepair.content.like(f'%{query_object.keywords}%'),
                )
            )

        # 时间范围查询
        if query_object.begin_time and query_object.end_time:
            try:
                begin_timestamp = int(datetime.fromisoformat(query_object.begin_time).timestamp())
                end_timestamp = int(datetime.fromisoformat(query_object.end_time + ' 23:59:59').timestamp())
                query = query.where(
                    and_(
                        OaPropertyRepair.repair_time >= begin_timestamp,
                        OaPropertyRepair.repair_time <= end_timestamp,
                    )
                )
            except ValueError:
                pass
        
        query = query.order_by(OaPropertyRepair.id.desc())
        
        repair_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return repair_list

    @classmethod
    async def add_property_repair_dao(cls, db: AsyncSession, repair: dict) -> OaPropertyRepair:
        """
        新增維修記錄數據庫操作

        :param db: orm 對象
        :param repair: 維修記錄字典
        :return:
        """
        # 排除關聯查詢字段，只保留數據庫表中存在的字段
        db_repair_data = {
            k: v for k, v in repair.items() 
            if k not in ['property_name', 'cate_name', 'brand_name', 'director_name']
        }
        db_repair = OaPropertyRepair(**db_repair_data)
        db.add(db_repair)
        await db.flush()

        return db_repair

    @classmethod
    async def edit_property_repair_dao(cls, db: AsyncSession, repair: dict) -> None:
        """
        編輯維修記錄數據庫操作

        :param db: orm 對象
        :param repair: 需要更新的維修記錄字典
        :return:
        """
        # 排除關聯查詢字段，只保留數據庫表中存在的字段
        db_repair_data = {
            k: v for k, v in repair.items() 
            if k not in ['property_name', 'cate_name', 'brand_name', 'director_name']
        }
        await db.execute(update(OaPropertyRepair), [db_repair_data])

    @classmethod
    async def delete_property_repair_dao(cls, db: AsyncSession, repair_id: int) -> None:
        """
        刪除維修記錄數據庫操作（邏輯刪除）

        :param db: orm 對象
        :param repair_id: 維修記錄 ID
        :return:
        """
        await db.execute(
            update(OaPropertyRepair)
            .where(OaPropertyRepair.id == repair_id)
            .values(delete_time=int(datetime.now().timestamp()))
        )
