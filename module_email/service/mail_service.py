import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
import os

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_email.entity.vo.mail_vo import SendMailResponseModel
from config.env import MailConfig


class MailService:
    """
    邮件模块服务层
    """

    @classmethod
    async def send_mail_service(cls, to_email: str, subject: str, content: str, is_html: bool = False) -> CrudResponseModel:
        # 添加发送间隔，避免触发频率限制
        await asyncio.sleep(1)  # 每封邮件间隔1秒
        """
        发送邮件service

        :param to_email: 收件人邮箱
        :param subject: 邮件主题
        :param content: 邮件内容
        :param is_html: 是否为HTML格式
        :return: 发送结果
        """
        try:
            # 创建邮件对象
            message = MIMEText(content, 'html' if is_html else 'plain', 'utf-8')
            # From字段使用正确格式，只对名称部分使用Header编码
            message['From'] = f'{Header(MailConfig.mail_sender_name, "utf-8").encode()} <{MailConfig.mail_sender_email}>'
            message['To'] = to_email
            message['Subject'] = Header(subject, 'utf-8')

            # 连接SMTP服务器并发送邮件
            with smtplib.SMTP_SSL(MailConfig.mail_smtp_server, MailConfig.mail_smtp_port) as server:
                server.login(MailConfig.mail_sender_email, MailConfig.mail_sender_password)
                server.sendmail(MailConfig.mail_sender_email, to_email, message.as_string())

            return CrudResponseModel(
                is_success=True,
                result=SendMailResponseModel(success=True, message='邮件发送成功'),
                message='邮件发送成功'
            )
        except smtplib.SMTPException as e:
            raise ServiceException(message=f'邮件发送失败: {str(e)}')
        except Exception as e:
            raise ServiceException(message=f'邮件发送异常: {str(e)}')

    @classmethod
    async def send_mail_with_attachment_service(cls, to_email: str, subject: str, content: str, file_path: str, is_html: bool = False) -> CrudResponseModel:
        # 添加发送间隔，避免触发频率限制
        await asyncio.sleep(1)  # 每封邮件间隔1秒
        """
        发送带附件的邮件service

        :param to_email: 收件人邮箱
        :param subject: 邮件主题
        :param content: 邮件内容
        :param file_path: 附件文件路径
        :param is_html: 是否为HTML格式
        :return: 发送结果
        """
        try:
            # 创建带附件的邮件对象
            message = MIMEMultipart()
            # From字段使用正确格式，只对名称部分使用Header编码
            message['From'] = f'{Header(MailConfig.mail_sender_name, "utf-8").encode()} <{MailConfig.mail_sender_email}>'
            message['To'] = to_email
            message['Subject'] = Header(subject, 'utf-8')

            # 添加邮件正文
            message.attach(MIMEText(content, 'html' if is_html else 'plain', 'utf-8'))

            # 添加附件
            if file_path and os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                with open(file_path, 'rb') as f:
                    attachment = MIMEApplication(f.read())
                    attachment.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', file_name))
                    message.attach(attachment)
            else:
                raise ServiceException(message='附件文件不存在')

            # 连接SMTP服务器并发送邮件
            with smtplib.SMTP_SSL(MailConfig.mail_smtp_server, MailConfig.mail_smtp_port) as server:
                server.login(MailConfig.mail_sender_email, MailConfig.mail_sender_password)
                server.sendmail(MailConfig.mail_sender_email, to_email, message.as_string())

            return CrudResponseModel(
                is_success=True,
                result=SendMailResponseModel(success=True, message='邮件发送成功'),
                message='邮件发送成功'
            )
        except smtplib.SMTPException as e:
            raise ServiceException(message=f'邮件发送失败: {str(e)}')
        except ServiceException as e:
            raise e
        except Exception as e:
            raise ServiceException(message=f'邮件发送异常: {str(e)}')