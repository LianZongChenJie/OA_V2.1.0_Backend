from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.purchased_dao import PurchasedDao
from module_admin.entity.vo.purchased_vo import (
    AddPurchasedModel,
    DeletePurchasedModel,
    EditPurchasedModel,
    PurchasedModel,
    PurchasedPageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class PurchasedService:
    """
    采购品管理服务层
    """

    @classmethod
    async def get_purchased_list_services(
            cls, query_db: AsyncSession, query_object: PurchasedPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取采购品列表信息 service（包含分类名称）

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 采购品列表信息对象
        """
        purchased_list_result = await PurchasedDao.get_purchased_list(query_db, query_object, is_page)
        
        # 如果返回的是分页数据，需要处理 rows 中的每一项
        if isinstance(purchased_list_result, PageModel):
            processed_rows = []
            for item in purchased_list_result.rows:
                # item 是一个列表 [采购品字典, 分类名称]
                if isinstance(item, (list, tuple)) and len(item) >= 1:
                    purchased_dict = item[0] if isinstance(item[0], dict) else CamelCaseUtil.transform_result(item[0])
                    cate_name = item[1] if len(item) > 1 else None
                    # 添加分类名称到采购品字典中
                    purchased_dict['cateName'] = cate_name if cate_name else ''
                    processed_rows.append(purchased_dict)
                elif isinstance(item, dict):
                    item['cateName'] = item.get('cate_name', '') or ''
                    processed_rows.append(item)
                else:
                    processed_rows.append(CamelCaseUtil.transform_result(item))
            
            purchased_list_result.rows = processed_rows
            return purchased_list_result
        else:
            # 如果不是分页数据，直接返回列表
            processed_list = []
            for item in purchased_list_result:
                if isinstance(item, (list, tuple)) and len(item) >= 1:
                    purchased_dict = item[0] if isinstance(item[0], dict) else CamelCaseUtil.transform_result(item[0])
                    cate_name = item[1] if len(item) > 1 else None
                    purchased_dict['cateName'] = cate_name if cate_name else ''
                    processed_list.append(purchased_dict)
                elif isinstance(item, dict):
                    item['cateName'] = item.get('cate_name', '') or ''
                    processed_list.append(item)
                else:
                    processed_list.append(CamelCaseUtil.transform_result(item))
            
            return processed_list

    @classmethod
    async def check_purchased_title_unique_services(
            cls, query_db: AsyncSession, page_object: PurchasedModel
    ) -> bool:
        """
        校验采购品名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 采购品对象
        :return: 校验结果
        """
        purchased_id = -1 if page_object.id is None else page_object.id
        purchased = await PurchasedDao.get_purchased_detail_by_info(query_db, page_object)
        if purchased and purchased.id != purchased_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_purchased_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddPurchasedModel, current_user_id: int = 0
    ) -> CrudResponseModel:
        """
        新增采购品信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增采购品对象
        :param current_user_id: 当前登录用户 ID
        :return: 新增采购品校验结果
        """
        if not await cls.check_purchased_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增采购品{page_object.title}失败，采购品名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_purchased = PurchasedModel(
                title=page_object.title,
                cate_id=page_object.cate_id if page_object.cate_id is not None else 0,
                thumb=page_object.thumb if page_object.thumb is not None else 0,
                code=page_object.code if page_object.code is not None else '',
                barcode=page_object.barcode if page_object.barcode is not None else '',
                unit=page_object.unit if page_object.unit is not None else '',
                specs=page_object.specs if page_object.specs is not None else '',
                brand=page_object.brand if page_object.brand is not None else '',
                producer=page_object.producer if page_object.producer is not None else '',
                purchase_price=page_object.purchase_price if page_object.purchase_price is not None else 0.00,
                sale_price=page_object.sale_price if page_object.sale_price is not None else 0.00,
                content=page_object.content,
                album_ids=page_object.album_ids if page_object.album_ids is not None else '',
                file_ids=page_object.file_ids if page_object.file_ids is not None else '',
                stock=page_object.stock if page_object.stock is not None else 0,
                is_object=page_object.is_object if page_object.is_object is not None else 1,
                status=page_object.status if page_object.status is not None else 1,
                create_time=current_time,
                update_time=current_time,
                delete_time=0
            )
            logger.info(f'Service 层准备插入的数据：title={add_purchased.title}, code={add_purchased.code}')
            await PurchasedDao.add_purchased_dao(query_db, add_purchased)
            await query_db.commit()
            logger.info(f'新增成功，生成的 ID: {add_purchased.id}')
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_purchased_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPurchasedModel
    ) -> CrudResponseModel:
        """
        编辑采购品信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑采购品对象
        :return: 编辑采购品校验结果
        """
        edit_purchased = page_object.model_dump(exclude_unset=True)
        purchased_info = await cls.purchased_detail_services(query_db, page_object.id)

        if purchased_info.id:
            if not await cls.check_purchased_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改采购品{page_object.title}失败，采购品名称已存在')

            try:
                edit_purchased['update_time'] = int(datetime.now().timestamp())
                await PurchasedDao.edit_purchased_dao(query_db, edit_purchased)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='采购品不存在')

    @classmethod
    async def delete_purchased_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeletePurchasedModel
    ) -> CrudResponseModel:
        """
        删除采购品信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除采购品对象
        :return: 删除采购品校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for purchased_id in id_list:
                    purchased = await cls.purchased_detail_services(query_db, int(purchased_id))
                    if not purchased.id:
                        raise ServiceException(message='采购品不存在')

                    update_time = int(datetime.now().timestamp())
                    await PurchasedDao.delete_purchased_dao(
                        query_db,
                        PurchasedModel(id=int(purchased_id), update_time=update_time),
                        page_object.type
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入采购品 id 为空')

    @classmethod
    async def set_purchased_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPurchasedModel
    ) -> CrudResponseModel:
        """
        设置采购品状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置采购品对象
        :return: 设置采购品状态校验结果
        """
        purchased_info = await cls.purchased_detail_services(query_db, page_object.id)

        if purchased_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await PurchasedDao.disable_purchased_dao(
                        query_db,
                        PurchasedModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await PurchasedDao.enable_purchased_dao(
                        query_db,
                        PurchasedModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='采购品不存在')

    @classmethod
    async def purchased_detail_services(cls, query_db: AsyncSession, purchased_id: int) -> PurchasedModel:
        """
        获取采购品详细信息 service

        :param query_db: orm 对象
        :param purchased_id: 采购品 id
        :return: 采购品 id 对应的信息
        """
        purchased = await PurchasedDao.get_purchased_detail_by_id(query_db, purchased_id)
        result = PurchasedModel(**CamelCaseUtil.transform_result(purchased)) if purchased else PurchasedModel()

        return result
