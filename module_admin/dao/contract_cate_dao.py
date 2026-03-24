from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.contract_cate_do import OaContractCate
from module_admin.entity.vo.contract_cate_vo import ContractCateModel, ContractCatePageQueryModel
from utils.page_util import PageUtil


class ContractCateDao:
    """
    合同类别管理模块数据库操作层
    """

    @classmethod
    async def get_contract_cate_detail_by_id(cls, db: AsyncSession, contract_cate_id: int) -> OaContractCate | None:
        """
        根据合同类别 id 获取合同类别详细信息

        :param db: orm 对象
        :param contract_cate_id: 合同类别 id
        :return: 合同类别信息对象
        """
        contract_cate_info = (
            (await db.execute(select(OaContractCate).where(OaContractCate.id == contract_cate_id)))
            .scalars()
            .first()
        )

        return contract_cate_info

    @classmethod
    async def get_contract_cate_detail_by_info(cls, db: AsyncSession, contract_cate: ContractCateModel) -> OaContractCate | None:
        """
        根据合同类别参数获取合同类别信息

        :param db: orm 对象
        :param contract_cate: 合同类别参数对象
        :return: 合同类别信息对象
        """
        query_conditions = []
        if contract_cate.title:
            query_conditions.append(OaContractCate.title == contract_cate.title)

        if query_conditions:
            contract_cate_info = (
                (await db.execute(select(OaContractCate).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            contract_cate_info = None

        return contract_cate_info

    @classmethod
    async def get_contract_cate_list(
            cls, db: AsyncSession, query_object: ContractCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取合同类别列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 合同类别列表信息对象
        """
        query = (
            select(OaContractCate)
            .where(
                OaContractCate.delete_time == 0,
                OaContractCate.title.like(f'%{query_object.title}%') if query_object.title else True,
                OaContractCate.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(OaContractCate.id)
            .distinct()
        )
        contract_cate_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return contract_cate_list

    @classmethod
    async def add_contract_cate_dao(cls, db: AsyncSession, contract_cate: ContractCateModel) -> OaContractCate:
        """
        新增合同类别数据库操作

        :param db: orm 对象
        :param contract_cate: 合同类别对象
        :return:
        """
        contract_cate_dict = contract_cate.model_dump(by_alias=False)
        db_contract_cate = OaContractCate(**contract_cate_dict)
        db.add(db_contract_cate)
        await db.flush()

        return db_contract_cate

    @classmethod
    async def edit_contract_cate_dao(cls, db: AsyncSession, contract_cate: dict) -> None:
        """
        编辑合同类别数据库操作

        :param db: orm 对象
        :param contract_cate: 需要更新的合同类别字典
        :return:
        """
        await db.execute(update(OaContractCate), [contract_cate])

    @classmethod
    async def delete_contract_cate_dao(cls, db: AsyncSession, contract_cate: ContractCateModel, del_type: int = 0) -> None:
        """
        删除合同类别数据库操作（逻辑删除）

        :param db: orm 对象
        :param contract_cate: 合同类别对象
        :param del_type: 删除类型
        :return:
        """
        update_time = contract_cate.update_time if contract_cate.update_time is not None else int(datetime.now().timestamp())
        delete_time = update_time
        await db.execute(
            update(OaContractCate)
            .where(OaContractCate.id.in_([contract_cate.id]))
            .values(status=-1, update_time=update_time, delete_time=delete_time)
        )

    @classmethod
    async def disable_contract_cate_dao(cls, db: AsyncSession, contract_cate: ContractCateModel) -> None:
        """
        禁用合同类别数据库操作

        :param db: orm 对象
        :param contract_cate: 合同类别对象
        :return:
        """
        update_time = contract_cate.update_time if contract_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaContractCate)
            .where(OaContractCate.id == contract_cate.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_contract_cate_dao(cls, db: AsyncSession, contract_cate: ContractCateModel) -> None:
        """
        启用合同类别数据库操作

        :param db: orm 对象
        :param contract_cate: 合同类别对象
        :return:
        """
        update_time = contract_cate.update_time if contract_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaContractCate)
            .where(OaContractCate.id == contract_cate.id)
            .values(status=1, update_time=update_time)
        )

