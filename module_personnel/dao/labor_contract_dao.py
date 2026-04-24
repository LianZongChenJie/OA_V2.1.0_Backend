from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from module_admin.entity.do.user_do import SysUser
from module_basicdata.entity.do.public.enterprise_do import OaEnterprise
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
        user = aliased(SysUser, name='user')
        query = (select(OaLaborContract,SysUser.nick_name.label('user_name'),user.nick_name.label('admin_name'),OaEnterprise.title.label('enterprise_name'))
                 .join(SysUser, OaLaborContract.uid == SysUser.user_id, isouter=True)
                 .join(user, user.user_id == OaLaborContract.admin_id, isouter=True)
                 .join(OaEnterprise, OaLaborContract.enterprise_id == OaEnterprise.id, isouter=True)
                     .where(
                            OaLaborContract.cate == query_object.cate if query_object.cate else True,
                            OaLaborContract.properties == query_object.properties if query_object.properties else True,
                            OaLaborContract.status == query_object.status if query_object.status else True,
                            OaLaborContract.types == query_object.types if query_object.types else True,
                            OaLaborContract.uid == query_object.uid if query_object.uid else True,
                            OaLaborContract.sign_time.between(
                                int(datetime.strptime(query_object.begin_time, "%Y-%m-%d").timestamp()),
                                int(datetime.strptime(query_object.end_time, "%Y-%m-%d").timestamp()),
                            ) if query_object.begin_time and query_object.end_time else True,

                        data_scope_sql,
            ).order_by(desc(OaLaborContract.create_time)))
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaLaborContractBaseModel):
        db_model = OaLaborContract(**model.model_dump(exclude={"id", "create_time",'sign_time','start_time', 'end_time', 'trial_end_time'}, exclude_none=True),
                                 create_time=model.create_time,
                                 sign_time=model.sign_time,
                                 start_time=model.start_time,
                                 end_time=model.end_time,
                                 trial_end_time = model.trial_end_time
                                   )
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, model: OaLaborContractBaseModel):
        result = await db.execute(
            update(OaLaborContract)
            .values(
                **model.model_dump(exclude={"id", "update_time",'sign_time','start_time', 'end_time', 'trial_end_time'}, exclude_none=True),
                        update_time=model.update_time,
                        sign_time = model.sign_time,
                        start_time = model.start_time,
                        end_time = model.end_time,
                        trial_end_time = model.trial_end_time
                    )
            .where(OaLaborContract.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        user = aliased(SysUser, name='user')
        query = (select(OaLaborContract,SysUser.nick_name.label('user_name'),user.nick_name.label('admin_name'),OaEnterprise.title.label('enterprise_name'))
                 .join(SysUser, OaLaborContract.uid == SysUser.user_id, isouter=True)
                 .join(user, user.user_id == OaLaborContract.admin_id, isouter=True)
                 .join(OaEnterprise, OaLaborContract.enterprise_id == OaEnterprise.id, isouter=True)
        .where(
            OaLaborContract.id == id))
        info = await db.execute(query)
        return info.mappings().first()

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaLaborContract).values(delete_time=int(datetime.now().timestamp())).where(OaLaborContract.id == id))
        await db.commit()
        return result.rowcount

