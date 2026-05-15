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
from module_basicdata.dao.public.template_dao import OaTemplateDao
from module_basicdata.entity.do.public.template_do import OaTemplate
from utils.camel_converter import ModelConverter


class MessageService:
    @classmethod
    async def get_list(cls, query_db: AsyncSession, query_object: OaMessagePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaMessageBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await MessageDao.get_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            query_list.rows = await cls.fields_handle(query_list.rows)
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
            return await cls._field_handle(detail)
        except Exception as e:
            raise e

    @classmethod
    async def add(cls, query_db: AsyncSession, create_model: OaMessageBaseModel):
        try:
            result = await MessageDao.add(query_db, create_model)
            if result.is_draft == 1:
                await cls.send(query_db, result.id)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            raise ServiceException('新增失败:' + str(e))

    @classmethod
    async def update(cls, query_db: AsyncSession, update_model: OaMessageBaseModel,):
        try:
            if not update_model.id:
                raise ServiceException('message_id不能为空')
            update_model.update_time = int(datetime.now().timestamp())
            await MessageDao.update(query_db, update_model)
            return CrudResponseModel(is_success=True, message='编辑成功')
        except Exception as e:
            raise ServiceException('编辑失败:' + str(e))

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

    @classmethod
    async def fields_handle(cls,fields_list:list[dict[str, Any]]):
        """
        列表查询字段处理
        :param fields_list:
        :return:
        """
        result_list = []
        for fields in fields_list:
            fields = dict(fields)
            fields.update(fields['OaMessage'].to_dict())
            fields.pop('OaMessage')
            flds = await cls._field_handle(fields)
            result_list.append(flds)
        return result_list

    @classmethod
    async def _field_handle(cls, fields: dict):
        """
        详情字段处理
        :param fields:
        :return:
        """
        if fields.get('to_names') is None:
            fields['to_names'] = ''
        elif fields['to_names'] == '':
            fields['to_names'] = ''
        else:
            # 可选：去除首尾逗号
            fields['to_names'] = fields['to_names'].strip(',')
            fields['to_names'] = fields['to_names'].replace(',,', ',')

        # 处理 copy_names
        if fields.get('copy_names') is None:
            fields['copy_names'] = ''
        elif fields['copy_names'] == '':
            fields['copy_names'] = ''
        else:
            # 可选：去除首尾逗号
            fields['copy_names'] = fields['copy_names'].strip(',')
            fields['copy_names'] = fields['copy_names'].replace(',,', ',')

        # 同样处理其他字段
        if fields.get('dept_names') is None:
            fields['dept_names'] = ''
        if fields.get('dept_names') is None:
            fields['dept_names'] = ''
        else:
            fields['dept_names'] = fields['dept_names'].strip(',')
            fields['dept_names'] = fields['dept_names'].replace(',,', ',')

        if fields.get('post_names') is None:
            fields['post_names'] = ''
        if fields.get('post_names') is None:
            fields['post_names'] = ''
        else:
            fields['post_names'] = fields['post_names'].strip(',')
            fields['post_names'] = fields['post_names'].replace(',,', ',')

        if fields['types'] == 1:
            fields['types_str'] = '用户'
            fields['to_user_name'] = fields['to_names']
        elif fields['types'] == 2:
            fields['types_str'] = '部门'
            fields['to_user_name'] = fields['dept_names']
        elif fields['types'] == 3:
            fields['types_str'] = '岗位'
            fields['to_user_name'] = fields['post_names']
        elif fields['types'] == 4:
            fields['types_str'] = '公司'
            fields['to_user_name'] = '全公司'

        return ModelConverter.convert_to_camel_case(fields)

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
                    camel_row = ModelConverter.convert_to_camel_case(row)
                    if camel_row['readTime'] is None:
                        camel_row['readTime'] = 0
                    row_list.append(camel_row)
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
            return CrudResponseModel(is_success=True, message='设置成功')
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


    @classmethod
    async def send_template_message(cls, query_db: AsyncSession, template_id: int, data: dict[str, Any], template_params: dict[str, Any]):
        """
        发送模板消息
        :param query_db:
        :param template_id:
        :param data: {'copy_uids':[1,2,3],'check_uids':[1,2,3],'user_id':'1','is_end':true,'check_status':2,'file_ids':'123','action_id':'1'} 消息接收人，审核状态等信息
        :param template_params: 模板字典{'title':'测试公告','from_user':'超级管理员', 'create_time':'2025-01-15 11:25:59', 'date':'2025-01-15 11:25:59'}
        :return:
        """
        message_list = []
        template = await OaTemplateDao.get_template_by_Id(query_db, template_id)
        if not template:
            raise ServiceException('发送模板消息失败，模板不存在！')

        if data.get('file_ids') is None:
            data['file_ids'] = ''
        if data.get('action_id') is None:
            data['action_id'] = 0

        if data.get('copy_uids') is not None:
            title,content = await cls.get_template_title_and_content(template, template_params['from_user'], template_params['create_time'], is_copy=True)
            result_list = await cls.send_template_add_list(data['copy_uids'], data['file_ids'],
                                             data['action_id'],title, content,template_id)
            message_list.extend(result_list)

        if data.get('check_uids') is not None:
            title, content = await cls.get_template_title_and_content(template, template_params['from_user'],
                                                                      template_params['create_time'], is_check=True)
            result_list = await cls.send_template_add_list(data['check_uids'], data['file_ids'],
                                                           data['action_id'], title, content, template_id)
            message_list.extend(result_list)

        if data.get('user_id'):
            is_end = False
            is_pass = False
            if data.get('is_end') is not None:
                is_end = data['is_end']
                if data.get('check_status'):
                    if data['check_status'] == 2:
                        is_pass = True
            title, content = await cls.get_template_title_and_content(template, template_params['from_user'],
                                                                      template_params['create_time'], is_user=True, is_end=is_end, is_pass=is_pass)
            result_list = await cls.send_template_add_list([data['user_id']], data['file_ids'],
                                                           data['action_id'], title, content, template_id)
            message_list.extend(result_list)

        try:
            await MsgDao.add_list(query_db, message_list)
        except Exception as e:
            raise ServiceException('发送失败:' + str(e))

    @classmethod
    async def send_template_add_list(cls, user_ids: list[int], file_ids: str, action_id: int, title:str, content:str, template_id:int):
        if user_ids is None:
            return []
        message_list = []
        try:
            for user_id in user_ids:
                msg = OaMsg()
                msg.title = title
                msg.template = template_id
                msg.content = content
                msg.file_ids = file_ids
                msg.from_uid = 0
                msg.to_uid = user_id
                msg.message_id = 0
                msg.msg_id = 0
                msg.is_star = 0
                msg.read_time = 0
                msg.create_time = int(datetime.now().timestamp())
                msg.action_id = action_id
                message_list.append(msg)
            return message_list
        except Exception as e:
            raise ServiceException('添加失败:' + str(e))

    @classmethod
    async def get_template_title_and_content(cls,template: OaTemplate, from_user:str, create_time:str, is_copy=False, is_check=False, is_user=False, is_end=False, is_pass=False):
        """
        通过模板生成通知title和content
        :param is_copy: 抄送人
        :param template: 模板
        :param is_check: 审核人
        :param is_user: 申请人
        :param is_end: 结束True，未结束False
        :param is_pass: 审核通过True，审核不通过False
        :param from_user: 申请人
        :param create_time: 申请时间
        :return:
        """
        if not template:
            raise ServiceException('模板不能为空')
        if is_copy:
            title = template.msg_title_3.replace('{from_user}', from_user)
            content = template.msg_content_3.replace('{create_time}', create_time).replace('{from_user}', from_user)
            return title, content
        if is_check:
            title = template.msg_title_0.replace('{from_user}', from_user)
            content = template.msg_content_0.replace('{create_time}', create_time).replace('{from_user}', from_user)
            return title, content
        if is_user:
            if is_end:
                if is_pass:
                    title = template.msg_title_1.replace('{from_user}', from_user)
                    content = template.msg_content_1.replace('{create_time}', create_time).replace('{from_user}', from_user)
                    return title, content
                else:
                    title = template.msg_title_2.replace('{from_user}', from_user)
                    content = template.msg_content_2.replace('{create_time}', create_time).replace('{from_user}', from_user)
                    return title, content
        return None, None



