from operator import and_

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from module_admin.entity.do.rewards_cate_do import SysRewardsCate
from module_admin.entity.do.user_do import SysUser
from utils.page_util import PageUtil
from module_personnel.entity.vo.rewards_vo import OaRewardsBaseModel, OaRewardsPageQueryModel
from module_personnel.entity.do.rewards_do import OaRewards
from typing import Any
from datetime import datetime

class RewardsDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaRewardsPageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        user = aliased(SysUser, name='user')
        query = (select(OaRewards,SysRewardsCate.title.label('cate_name'),SysUser.nick_name.label('user_name'), user.nick_name.label('admin_name'))
                 .join(SysRewardsCate, OaRewards.rewards_cate == SysRewardsCate.id,isouter=True)\
                 .join(SysUser, OaRewards.uid == SysUser.user_id,isouter=True)
                 .join(user, OaRewards.admin_id == user.user_id,isouter=True)
                     .where(
                            OaRewards.status == query_object.status if query_object.status else True,
                            OaRewards.types == query_object.types if query_object.types else True,
                            OaRewards.rewards_cate == query_object.rewards_cate if query_object.rewards_cate else True,
                            OaRewards.uid == query_object.uid if query_object.uid else True,
                            OaRewards.cate == query_object.cate if query_object.cate else True,
                            OaRewards.remark.like('%' + query_object.remark + '%') if query_object.remark else True,
                            OaRewards.check_time.between(
                                int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                                int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                            ) if query_object.begin_time and query_object.end_time else True,
                        data_scope_sql,
            ).order_by(desc(OaRewards.create_time)))
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaRewardsBaseModel):
        db_model = OaRewards(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                                 create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, model: OaRewardsBaseModel):
        result = await db.execute(
            update(OaRewards)
            .values(
                **model.model_dump(exclude={"id", "update_time"}, exclude_none=True,),update_time=model.update_time
            )
            .where(OaRewards.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaRewards)
        .where(
            OaRewards.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_uid(cls, db: AsyncSession, model: OaRewardsBaseModel) -> OaRewards | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_info = (
            (
                await db.execute(
                    select(OaRewards)
                    .where(
                        OaRewards.uid == model.uid if model.uid else True
                        and OaRewards.check_status != 2 if model.check_status else True
                    )
                    .order_by(desc(OaRewards.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaRewards).values(delete_time=int(datetime.now().timestamp())).where(OaRewards.id == id))
        await db.commit()
        return result.rowcount

