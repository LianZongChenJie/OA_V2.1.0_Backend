from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from module_basicdata.entity.do.public.enterprise_do import OaEnterprise
from sqlalchemy import select, update, desc
from typing import Any
from common.vo import PageModel
from module_basicdata.entity.vo.public.enterprise_vo import OaEnterpriseBaseModel
from utils.page_util import PageUtil


class EnterpriseDao:
    @classmethod
    async def get_enterprise_list(cls, db: AsyncSession, query_object: OaEnterpriseBaseModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaEnterprise)
                 .where(
                    OaEnterprise.status != "-1"
                 if query_object
                 else True,
                 data_scope_sql,
                 ).order_by(OaEnterprise.id.asc()))
        enterprise_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return enterprise_list

    @classmethod
    async def add_enterprise(cls, db: AsyncSession, model: OaEnterpriseBaseModel):
        db_enterprise = OaEnterprise(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True), create_time = model.create_time)
        db.add(db_enterprise)
        await db.commit()
        await db.refresh(db_enterprise)
        return db_enterprise
        pass

    @classmethod
    async def update_enterprise(cls, db: AsyncSession, model: OaEnterpriseBaseModel):
        result = await db.execute(
            update(OaEnterprise)
            .values(**model.model_dump(exclude={"id", "update_time"}, exclude_none=True), update_time = model.update_time)
            .where(OaEnterprise.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def delete_enterprise(cls, db: AsyncSession, id: int):
        result = await db.execute(
            update(OaEnterprise).values(status="-1").where(OaEnterprise.id == id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_enterprise_info(cls, db: AsyncSession, id: int):
        query = (select(OaEnterprise)
                .where(
                    OaEnterprise.id == id,
                    OaEnterprise.status != "-1"))
        enterprise_info = await db.scalar(query)
        return enterprise_info

    @classmethod
    async def change_status_enterprise(cls, db: AsyncSession, model: OaEnterpriseBaseModel):
        result = await db.execute(
            update(OaEnterprise).values(status=model.status).where(OaEnterprise.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_title(cls, db: AsyncSession, model: OaEnterpriseBaseModel) -> OaEnterprise | None:
        """
        根据标题用户信息

        :param model:
        :param db: orm对象
        :return: 对象
        """
        query_info = (
            (
                await db.execute(
                    select(OaEnterprise)
                    .where(
                        OaEnterprise.status == '1',
                        OaEnterprise.title == model.title if model.title else True
                    )
                    .order_by(desc(OaEnterprise.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info