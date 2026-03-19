from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.contract_cate_dao import ContractCateDao
from module_admin.entity.vo.contract_cate_vo import (
    AddContractCateModel,
    DeleteContractCateModel,
    EditContractCateModel,
    ContractCateModel,
    ContractCatePageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class ContractCateService:
    """
    合同类别管理模块服务层
    """

    @classmethod
    async def get_contract_cate_list_services(
            cls, query_db: AsyncSession, query_object: ContractCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取合同类别列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 合同类别列表信息对象
        """
        contract_cate_list_result = await ContractCateDao.get_contract_cate_list(query_db, query_object, is_page)

        return contract_cate_list_result

    @classmethod
    async def check_contract_cate_title_unique_services(
            cls, query_db: AsyncSession, page_object: ContractCateModel
    ) -> bool:
        """
        校验合同类别名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 合同类别对象
        :return: 校验结果
        """
        contract_cate_id = -1 if page_object.id is None else page_object.id
        contract_cate = await ContractCateDao.get_contract_cate_detail_by_info(query_db, page_object)
        if contract_cate and contract_cate.id != contract_cate_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_contract_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddContractCateModel
    ) -> CrudResponseModel:
        """
        新增合同类别信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增合同类别对象
        :return: 新增合同类别校验结果
        """
        if not await cls.check_contract_cate_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增合同类别{page_object.title}失败，合同类别名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_contract_cate = ContractCateModel(
                title=page_object.title,
                status=page_object.status if page_object.status is not None else 1,
                create_time=current_time,
                update_time=current_time,
                delete_time=0
            )
            logger.info(f'Service 层准备插入的数据：title={add_contract_cate.title}, create_time={add_contract_cate.create_time}, update_time={add_contract_cate.update_time}, delete_time={add_contract_cate.delete_time}')
            await ContractCateDao.add_contract_cate_dao(query_db, add_contract_cate)
            await query_db.commit()
            logger.info(f'新增成功，生成的 ID: {add_contract_cate.id}')
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_contract_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditContractCateModel
    ) -> CrudResponseModel:
        """
        编辑合同类别信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑合同类别对象
        :return: 编辑合同类别校验结果
        """
        edit_contract_cate = page_object.model_dump(exclude_unset=True)
        contract_cate_info = await cls.contract_cate_detail_services(query_db, page_object.id)

        if contract_cate_info.id:
            if not await cls.check_contract_cate_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改合同类别{page_object.title}失败，合同类别名称已存在')

            try:
                edit_contract_cate['update_time'] = int(datetime.now().timestamp())
                await ContractCateDao.edit_contract_cate_dao(query_db, edit_contract_cate)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='合同类别不存在')

    @classmethod
    async def delete_contract_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteContractCateModel
    ) -> CrudResponseModel:
        """
        删除合同类别信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除合同类别对象
        :return: 删除合同类别校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for contract_cate_id in id_list:
                    contract_cate = await cls.contract_cate_detail_services(query_db, int(contract_cate_id))
                    if not contract_cate.id:
                        raise ServiceException(message='合同类别不存在')

                    update_time = int(datetime.now().timestamp())
                    await ContractCateDao.delete_contract_cate_dao(
                        query_db,
                        ContractCateModel(id=int(contract_cate_id), update_time=update_time),
                        page_object.type
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入合同类别 id 为空')

    @classmethod
    async def set_contract_cate_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditContractCateModel
    ) -> CrudResponseModel:
        """
        设置合同类别状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置合同类别状态对象
        :return: 设置合同类别状态校验结果
        """
        contract_cate_info = await cls.contract_cate_detail_services(query_db, page_object.id)

        if contract_cate_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await ContractCateDao.disable_contract_cate_dao(
                        query_db,
                        ContractCateModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await ContractCateDao.enable_contract_cate_dao(
                        query_db,
                        ContractCateModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='合同类别不存在')

    @classmethod
    async def contract_cate_detail_services(cls, query_db: AsyncSession, contract_cate_id: int) -> ContractCateModel:
        """
        获取合同类别详细信息 service

        :param query_db: orm 对象
        :param contract_cate_id: 合同类别 id
        :return: 合同类别 id 对应的信息
        """
        contract_cate = await ContractCateDao.get_contract_cate_detail_by_id(query_db, contract_cate_id)
        result = ContractCateModel(**CamelCaseUtil.transform_result(contract_cate)) if contract_cate else ContractCateModel()

        return result

