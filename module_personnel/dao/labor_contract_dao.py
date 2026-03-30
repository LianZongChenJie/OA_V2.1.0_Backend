from operator import and_

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from utils.page_util import PageUtil
from module_personnel.entity.vo.lable_contract_vo import OaLaborContractBaseModel, OaLaborContractPageQueryModel
from module_personnel.entity.do.labor_contract_do import OaLaborContract
from typing import Any
from datetime import datetime

class LaborContractDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaLaborContractPageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaLaborContract)
                     .where(
                        and_(
                            OaLaborContract.status == query_object.status if query_object.status else True,
                            OaLaborContract.types == query_object.types if query_object.types else True,
                            OaLaborContract.rewards_cate == query_object.rewards_cate if query_object.rewards_cate else True,
                            OaLaborContract.uid == query_object.uid if query_object.uid else True,
                            OaLaborContract.check_time.between(
                                int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                                int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                            ) if query_object.begin_time and query_object.end_time else True,

                        ),
                        data_scope_sql,
            ).order_by(desc(OaLaborContract.create_time)))
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaLaborContractBaseModel):
        db_model = OaLaborContract(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                                 create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaLaborContractBaseModel):
        result = await db.execute(
            update(OaLaborContract)
            .values(
                **model.model_dump(exclude={"id", "create_time"}, exclude_none=True, update_time=model.update_time)
            )
            .where(OaLaborContract.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaLaborContract)
        .where(
            OaLaborContract.id == id))
        info = await db.scalar(query)
        return info

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaLaborContract).values(delete_time=int(datetime.now().timestamp())).where(OaLaborContract.id == id))
        await db.commit()
        return result.rowcount

