from fastapi import Request, Response

from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import DynamicResponseModel
from module_email.entity.vo.mail_vo import SendMailModel, SendMailResponseModel
from module_email.service.mail_service import MailService
from utils.log_util import logger
from utils.response_util import ResponseUtil

mail_controller = APIRouterPro(prefix='/mail', order_num=17, tags=['邮件模块'], dependencies=[PreAuthDependency()])


@mail_controller.post(
    '/send',
    summary='发送邮件接口',
    description='用于发送邮件',
    response_model=DynamicResponseModel[SendMailResponseModel],
)
async def send_mail(request: Request, mail_info: SendMailModel) -> Response:
    send_result = await MailService.send_mail_service(
        mail_info.to_email,
        mail_info.subject,
        mail_info.content,
        mail_info.is_html
    )
    logger.info('邮件发送成功')

    return ResponseUtil.success(model_content=send_result.result)
