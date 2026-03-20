from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, update, desc, asc
from typing import Any
from common.vo import PageModel
from utils.page_util import PageUtil
from module_basicdata.entity.vo.project.work_cate_vo import WorkCatePageQueryModel, OaWorkCateBaseModel
from module_basicdata.entity.do.project.work_cate_do import OaWorkCate

class WorkCateDao:

    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: WorkCatePageQueryModel, data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaWorkCate)
                 .where(
            data_scope_sql,
        ).order_by(asc(OaWorkCate.create_time)))
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaWorkCateBaseModel):
        db_model = OaWorkCate(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True), create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaWorkCateBaseModel):
        result = await db.execute(
            update(OaWorkCate)
            .values(
                title = model.title,
                update_time = model.update_time,
            )
            .where(OaWorkCate.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def change_status(cls, db: AsyncSession, model: OaWorkCateBaseModel):
        result = await db.execute(
            update(OaWorkCate).values(status = model.status).where(OaWorkCate.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaWorkCate)
        .where(
            OaWorkCate.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_title(cls, db: AsyncSession, model: OaWorkCateBaseModel) -> OaWorkCate | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_info = (
            (
                await db.execute(
                    select(OaWorkCate)
                    .where(
                        OaWorkCate.title == model.title if model.title else True
                    )
                    .order_by(desc(OaWorkCate.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info