from datetime import datetime
from typing import Any, List

from sqlalchemy import and_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.website_account_do import OaWebsiteAccount
from module_admin.entity.vo.website_account_vo import (
    WebsiteAccountPageQueryModel, AddWebsiteAccountModel,
    EditWebsiteAccountModel, DeleteWebsiteAccountModel,
    SetWebsiteAccountStatusModel
)
from utils.page_util import PageUtil

class WebsiteAccountDao:
    """网站账号管理模块数据库操作层"""

    @classmethod
    async def get_website_account_list(
            cls, db: AsyncSession, query_object: WebsiteAccountPageQueryModel, is_page: bool = False
    ) -> PageModel | List[OaWebsiteAccount]:
        """获取网站账号信息列表"""
        query = select(OaWebsiteAccount).where(OaWebsiteAccount.delete_time == 0)

        # 添加查询条件
        if query_object.website_url and query_object.website_url.strip():
            query = query.where(OaWebsiteAccount.website_url.like(f'%{query_object.website_url.strip()}%'))

        # 排序
        query = query.order_by(OaWebsiteAccount.sort.asc())

        if is_page:
            result = await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size)
        else:
            result = (await db.execute(query)).scalars().all()

        return result

    @classmethod
    async def get_website_account_detail_by_id(cls, db: AsyncSession, account_id: int) -> OaWebsiteAccount | None:
        """根据 ID 获取网站账号信息详情"""
        query = select(OaWebsiteAccount).where(
            OaWebsiteAccount.id == account_id, OaWebsiteAccount.delete_time == 0
        )
        result = (await db.execute(query)).scalars().first()
        return result

    @classmethod
    async def add_website_account_dao(cls, db: AsyncSession, account: AddWebsiteAccountModel) -> OaWebsiteAccount:
        """新增网站账号信息"""
        now = datetime.now()
        db_account = OaWebsiteAccount(
            **account.model_dump(exclude_unset=True, by_alias=True),
            create_time=int(now.timestamp()),
            update_time=int(now.timestamp()),
            delete_time=0
        )
        db.add(db_account)
        await db.flush()
        await db.refresh(db_account)
        return db_account

    @classmethod
    async def edit_website_account_dao(cls, db: AsyncSession, account: EditWebsiteAccountModel) -> OaWebsiteAccount:
        """编辑网站账号信息"""
        # 构建更新数据，排除不需要更新的字段
        edit_data = account.model_dump(exclude_unset=True, exclude={'id'}, by_alias=True)
        
        # 移除不应该由编辑接口修改的字段
        edit_data.pop('created_at', None)  # 创建时间不应修改
        edit_data.pop('updated_at', None)  # 更新时间由数据库自动管理
        edit_data.pop('create_time', None)  # 创建时间戳不应修改
        edit_data.pop('delete_time', None)  # 删除时间不应通过编辑修改
        
        # 设置更新时间戳
        edit_data['update_time'] = int(datetime.now().timestamp())

        # MySQL 不支持 RETURNING 子句，需要先更新再查询
        query = (
            update(OaWebsiteAccount)
            .where(OaWebsiteAccount.id == account.id, OaWebsiteAccount.delete_time == 0)
            .values(**edit_data)
        )
        await db.execute(query)
        await db.flush()
        
        # 重新查询获取更新后的数据
        updated_account = await cls.get_website_account_detail_by_id(db, account.id)
        return updated_account

    @classmethod
    async def delete_website_account_dao(cls, db: AsyncSession, account_ids: List[int], delete_time: int):
        """软删除网站账号信息"""
        stmt = update(OaWebsiteAccount).where(OaWebsiteAccount.id.in_(account_ids)).values(
            delete_time=delete_time,
            update_time=int(datetime.now().timestamp())
        )
        await db.execute(stmt)

    @classmethod
    async def set_website_account_status_dao(
            cls, db: AsyncSession, account_id: int, status: int
    ) -> OaWebsiteAccount | None:
        """设置网站账号状态"""
        update_data = {
            'status': str(status),
            'update_time': int(datetime.now().timestamp())
        }
        query = (
            update(OaWebsiteAccount)
            .where(OaWebsiteAccount.id == account_id, OaWebsiteAccount.delete_time == 0)
            .values(**update_data)
            .returning(OaWebsiteAccount)
        )
        result = await db.execute(query)
        await db.flush()
        return result.scalar()
