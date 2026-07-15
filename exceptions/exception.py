class LoginException(Exception):
    """
    自定义登录异常LoginException
    """

    def __init__(self, data: str | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self.data = data
        self.message = message

    def __str__(self) -> str:
        return self.message or ''


class AuthException(Exception):
    """
    自定义令牌异常AuthException
    """

    def __init__(self, data: str | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self.data = data
        self.message = message

    def __str__(self) -> str:
        return self.message or ''


class PermissionException(Exception):
    """
    自定义权限异常PermissionException
    """

    def __init__(self, data: str | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self.data = data
        self.message = message

    def __str__(self) -> str:
        return self.message or ''


class ServiceException(Exception):
    """
    自定义服务异常ServiceException
    """

    def __init__(self, data: str | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self.data = data
        self.message = message

    def __str__(self) -> str:
        return self.message or ''


class ServiceWarning(Exception):
    """
    自定义服务警告ServiceWarning
    """

    def __init__(self, data: str | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self.data = data
        self.message = message

    def __str__(self) -> str:
        return self.message or ''


class ModelValidatorException(Exception):
    """
    自定义模型校验异常ModelValidatorException
    """

    def __init__(self, data: str | None = None, message: str | None = None) -> None:
        super().__init__(message)
        self.data = data
        self.message = message

    def __str__(self) -> str:
        return self.message or ''
