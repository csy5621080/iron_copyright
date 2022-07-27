from utils.tools import BaseError


class UserError(BaseError):

    def __init__(self):
        self.code = 12000


class UserPasswordError(UserError):

    def __init__(self):
        super(UserPasswordError, self).__init__()
        self.code += 9
        self.msg = "密码错误"


class UserNotExist(UserError):

    def __init__(self):
        super(UserNotExist, self).__init__()
        self.code += 10
        self.msg = "用户不存在"


class UserNotLogin(UserError):

    def __init__(self):
        super(UserNotLogin, self).__init__()
        self.code += 1
        self.msg = "用户未登录"


