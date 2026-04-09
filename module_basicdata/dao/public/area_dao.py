from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from module_basicdata.entity.do.public.arae_do import OaArea
from module_basicdata.entity.vo.public.area_vo import AreaBaseModel, AreaTreeModel

from typing import List, Dict


class AreaDao:
    @classmethod
    async def get_area_tree(cls, db : AsyncSession, area: AreaBaseModel) -> list[AreaTreeModel]:
        """
        将区域列表转换为树形结构

        :param area_list: 区域列表
        :return: 树形结构的区域列表
        """
        areas = await cls.get_list(db, area)
        # 构建ID到节点的映射
        node_map = {}
        for area in areas:
            node_map[area.id] = {
                'id': area.id,
                'pid': area.pid,
                'name': area.name,
                'shortname': area.shortname,
                'level': area.level,
                'longitude': area.longitude,
                'latitude': area.latitude,
                'sort': area.sort,
                'children': []
            }

        # 构建树
        tree = []
        for area in areas:
            node = node_map[area.id]
            if area.pid == area.pid:
                tree.append(node)
            else:
                if area.pid in node_map:
                    node_map[area.pid]['children'].append(node)

        # 对每个节点的子节点排序
        cls._sort_children(tree)

        return tree

    @classmethod
    def _sort_children(cls, nodes: List[Dict]):
        """递归排序子节点"""
        nodes.sort(key=lambda x: (x['level'], x['sort'], x['id']))
        for node in nodes:
            if node['children']:
                cls._sort_children(node['children'])

    @classmethod
    async def get_list(cls, db: AsyncSession, area: AreaBaseModel) -> list[AreaBaseModel]:
        query = (select(OaArea)
        .where(
            OaArea.status == "1",
            OaArea.pid == area.pid if area.pid else True,))
        result = await db.execute(query)
        area_list = result.scalars().all()
        return area_list

    @classmethod
    async def get_by_id(cls, db: AsyncSession, id: int) -> AreaBaseModel:
        query = (select(OaArea).filter(OaArea.id == id))
        result = await db.execute(query)
        area = result.scalar()
        return area

    @classmethod
    async def add(cls, db: AsyncSession, area: AreaBaseModel) -> AreaTreeModel:
        db_area = OaArea(**area.model_dump(exclude={"id"}, exclude_none=True))
        db.add(db_area)
        await db.commit()
        await db.refresh(db_area)
        return db_area

    @classmethod
    async def update(cls, db: AsyncSession, area: AreaBaseModel) -> AreaTreeModel:
        result = await db.execute(
            update(OaArea)
            .values(**area.model_dump(exclude={"id"}, exclude_none=True))
            .where(OaArea.id == area.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def delete(cls, db: AsyncSession, id: int) -> AreaTreeModel:
        result = await db.execute(
            update(OaArea)
            .values(status="-1")
            .where(OaArea.id == id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def change_status_area(cls, db: AsyncSession, model: AreaBaseModel) -> AreaTreeModel:
        result = await db.execute(
            update(OaArea).values(status=model.status).where(OaArea.id == model.id)
        )
        await db.commit()
        return result.rowcount


    @classmethod
    async def get_area_by_level(cls, db: AsyncSession, level: int) -> AreaBaseModel:
        query = (select(OaArea).filter(OaArea.level == level))
        result = await db.execute(query)
        area = result.scalars().all()
        return area

    @classmethod
    async def get_info_by_title(cls, db: AsyncSession, model: AreaBaseModel) -> OaArea | None:
        """
        根据标题用户信息

        :param model:
        :param db: orm对象
        :return: 对象
        """
        query_info = (
            (
                await db.execute(
                    select(OaArea)
                    .where(
                        OaArea.status == '1',
                        OaArea.pid == model.pid if model.pid else True,
                        OaArea.name == model.name if model.name else True
                    )
                    .order_by(desc(OaArea.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info