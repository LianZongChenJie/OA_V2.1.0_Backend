from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SendMailModel(BaseModel):
    """
    发送邮件请求模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    to_email: str = Field(description='收件人邮箱')
    subject: str = Field(description='邮件主题')
    content: str = Field(description='邮件内容')
    is_html: bool = Field(default=False, description='是否为HTML格式')


class SendMailResponseModel(BaseModel):
    """
    发送邮件响应模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    success: bool = Field(description='发送是否成功')
    message: str = Field(description='响应信息')
