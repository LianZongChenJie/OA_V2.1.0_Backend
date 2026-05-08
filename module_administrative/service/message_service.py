from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from common.vo import PageModel, CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.dao.user_dao import UserDao
from module_administrative.dao.message_dao import MessageDao
from module_administrative.dao.msg_dao import MsgDao
from module_administrative.entity.do.msg_do import OaMsg
from module_administrative.entity.vo.message_vo import OaMessageBaseModel, OaMessagePageQueryModel
from typing import Any
from datetime import datetime

from module_administrative.entity.vo.msg_vo import OaMsgQueryPageModel
from utils.camel_converter import ModelConverter


class MessageService:
    @classmethod
    async def get_list(cls, query_db: AsyncSession, query_object: OaMessagePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaMessageBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await MessageDao.get_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            row_list = []
            for row in query_list.rows:
                row = dict(row)
                row.update(row['OaMessage'].to_dict())
                row.pop('OaMessage')
                if row['types'] == 1:
                    row['types_str'] = '用户'
                    row['to_user_name'] = row['to_name']
                elif row['types'] == 2:
                    row['types_str'] = '部门'
                    row['to_user_name'] = row['dept_name']
                elif row['types'] == 3:
                    row['types_str'] = '岗位'
                    row['to_user_name'] = row['post_name']
                elif row['types'] == 4:
                    row['types_str'] = '公司'
                    row['to_user_name'] = '全公司'
                row_list.append(ModelConverter.convert_to_camel_case(row))
            query_list.rows = row_list
            return query_list
        else:
            return ModelConverter.convert_to_camel_case(query_list)

    @classmethod
    async def get_send_detail(cls, query_db: AsyncSession, message_id: int):
        try:
            if not message_id:
                raise ServiceException('message_id不能为空')
            detail = await MessageDao.get_detail(query_db, message_id)
            detail = dict(detail)
            detail.update(detail['OaMessage'].to_dict())
            detail.pop('OaMessage')
            if detail['types'] == 1:
                detail['types_str'] = '用户'
                detail['to_user_name'] = detail['to_name']
            elif detail['types'] == 2:
                detail['types_str'] = '部门'
                detail['to_user_name'] = detail['dept_name']
            elif detail['types'] == 3:
                detail['types_str'] = '岗位'
                detail['to_user_name'] = detail['post_name']
            elif detail['types'] == 4:
                detail['types_str'] = '公司'
                detail['to_user_name'] = '全公司'
            return ModelConverter.convert_to_camel_case(detail)
        except Exception as e:
            raise e

    @classmethod
    async def add(cls, query_db: AsyncSession, create_model: OaMessageBaseModel):
        try:
            result = await MessageDao.add(query_db, create_model)
            if result.is_draft == 1:
                await cls.send(query_db, result.id)
            return CrudResponseModel(is_success=True, message='添加成功')
        except Exception as e:
            raise ServiceException('添加失败:' + str(e))

    @classmethod
    async def update(cls, query_db: AsyncSession, update_model: OaMessageBaseModel,):
        try:
            if not update_model.id:
                raise ServiceException('message_id不能为空')
            update_model.update_time = int(datetime.now().timestamp())
            await MessageDao.update(query_db, update_model)
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            raise ServiceException('更新失败:' + str(e))

    @classmethod
    async def delete(cls, query_db: AsyncSession, message_ids: list[int], table: str):
        try:
            if not message_ids:
                raise ServiceException('message_id不能为空')
            if table == 'message':
                await MessageDao.delete(query_db, message_ids)
            elif table == 'msg':
                await MsgDao.delete(query_db, message_ids)
            else:
                raise ServiceException('table参数错误')
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            raise ServiceException('删除失败:' + str(e))

    @classmethod
    async def restore(cls, query_db: AsyncSession, message_id: int, table: str):
        try:
            if not message_id:
                raise ServiceException('message_id不能为空')
            if table == 'message':
                await MessageDao.restore(query_db, message_id)
            elif table == 'msg':
                await MsgDao.restore(query_db, message_id)
            return CrudResponseModel(is_success=True, message='恢复成功')
        except Exception as e:
            raise ServiceException('恢复失败:' + str(e))

    @classmethod
    async def clear(cls, query_db: AsyncSession, message_id: int, table: str):
        try:
            if not message_id:
                raise ServiceException('message_id不能为空')
            if table == 'message':
                await MessageDao.clear(query_db, message_id)
            elif table == 'msg':
                await MsgDao.clear(query_db, message_id)
            else:
                raise ServiceException('table参数错误')
            return CrudResponseModel(is_success=True, message='清除成功')
        except Exception as e:
            raise ServiceException('清除失败:' + str(e))

    @classmethod
    async def send(cls, query_db: AsyncSession, message_id: int):
        try:
            if not message_id:
                raise ServiceException('message_id不能为空')
            message = await MessageDao.get_detail(query_db, message_id)
            message = message['OaMessage']
            msg = OaMsg()
            msg.title = message.title
            msg.content = message.content
            msg.from_uid = message.from_uid
            msg.file_ids = message.file_ids
            msg.create_time = int(datetime.now().timestamp())
            msg.from_uid = message.from_uid
            msg.message_id = message_id
            msg.is_star = 0
            msg.clear_time = 0
            msg.action_id = 0
            if message.types == 1:
                to_uids = message.uids.split(',')
                for to_uid in to_uids:
                    msg.to_uid = to_uid
                    await MsgDao.add_by_entity(query_db, msg)
            elif message.types == 2:
                dept_ids = message.dids.split(',')
                for dept_id in dept_ids:
                    user_ids = await UserDao.get_user_id_by_dept_id(query_db, dept_id)
                    for user_id in user_ids:
                        msg.to_uid = user_id
                        await MsgDao.add_by_entity(query_db, msg)
            elif message.types == 3:
                post_ids = message.post_ids.split(',')
                for post_id in post_ids:
                    user_ids = await UserDao.get_user_id_by_post_id(query_db, post_id)
                    for user_id in user_ids:
                        msg.to_uid = user_id
                        await MsgDao.add_by_entity(query_db, msg)
            elif message.types == 4:
                user_ids = await UserDao.get_all_user_id(query_db)
                for user_id in user_ids:
                    msg.to_uid = user_id
                    await MsgDao.add_by_entity(query_db, msg)
            message.send_time = int(datetime.now().timestamp())
            message.is_draft = 1
            await MessageDao.update_by_entity(query_db, message)
            return CrudResponseModel(is_success=True, message='发送成功')
        except Exception as e:
            raise e

# ---------------------------------------------- 垃圾箱 -----------------------------------------------------
    @classmethod
    async def get_rubbish_list(cls, query_db: AsyncSession, user_id:int, query_model: OaMessagePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaMessageBaseModel] | \
                                                                                             list[dict[str, Any]]:
        """
        获取回收站消息列表
        :param query_db:
        :param user_id:
        :param query_model:
        :param data_scope_sql:
        :param is_page:
        :return:
        """
        try:
            # 获取收件箱删除消息
            delete_list = await MessageDao.get_delete_msg(query_db,  user_id,query_model, data_scope_sql, is_page)
            row_list = []
            for row in delete_list.rows:
                row = dict(row)
                row_list.append(ModelConverter.convert_to_camel_case(row))
            delete_list.rows = row_list
            return delete_list
        except Exception as e:
            raise e

# ---------------------------------------------- 收件箱 -----------------------------------------------------
    @classmethod
    async def get_receive_list(cls, query_db: AsyncSession, query_model:OaMsgQueryPageModel, data_scope_sql: ColumnElement,
                       is_page: bool = False) -> PageModel[OaMessageBaseModel] | list[dict[str, Any]]:
        """
        获取收件箱消息列表
        :param query_db:
        :param query_model:
        :param data_scope_sql:
        :param is_page:
        :return:
        """
        try:
            # 获取收件箱消息
            receive_list = await MsgDao.get_page_list(query_db,  query_model, data_scope_sql, is_page)
            if is_page:
                row_list = []
                for row in receive_list.rows:
                    row = dict(row)
                    row.update(row['OaMsg'].to_dict())
                    row.pop('OaMsg')
                    row_list.append(ModelConverter.convert_to_camel_case(row))
                receive_list.rows = row_list
            return ModelConverter.convert_to_camel_case(receive_list)
        except Exception as e:
            raise ServiceException('查询收件箱失败:' + str(e))

    @classmethod
    async def set_star(cls, query_db: AsyncSession, message_ids: list[int], is_star: int):
        """
        设置消息是否标星
        :param query_db:
        :param message_ids:
        :param is_star:
        :return:
        """
        try:
            if not message_ids:
                raise ServiceException('message_id不能为空')
            await MsgDao.set_star(query_db, message_ids, is_star)
            return CrudResponseModel(is_success=True, message='设置成功')
        except Exception as e:
            raise ServiceException('设置失败:' + str(e))


    @classmethod
    async def set_read(cls, query_db: AsyncSession, message_id: int):
        """
        单个消息查看
        :param query_db:
        :param message_id:
        :return:
        """
        try:
            if not message_id:
                raise ServiceException('message_id不能为空')
            await MsgDao.set_read(query_db, [message_id])
            result = await MsgDao.get_msg_by_id(query_db, message_id)
            result = dict(result)
            result.update(result['OaMsg'].to_dict())
            result.pop('OaMsg')
            return ModelConverter.convert_to_camel_case(result)
        except Exception as e:
            raise ServiceException('阅读失败:' + str(e))

    @classmethod
    async def set_reads(cls, query_db: AsyncSession, message_ids: list[int]):
        """
        批量消息查看
        :param query_db:
        :param message_ids:
        :return:
        """
        try:
            if not message_ids:
                raise ServiceException('message_id不能为空')
            await MsgDao.set_read(query_db, message_ids)
            return CrudResponseModel(is_success=True, message='设置成功')
        except Exception as e:
            raise ServiceException('阅读失败:' + str(e))