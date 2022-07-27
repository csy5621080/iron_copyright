from ninja import Router
from .schema import *
from .models import User
from .exceptions import *
from utils.tools import make_password
user_api = Router()


@user_api.post("/login/", response=LoginResponse, auth=None, description="管理员登录接口, 输入账号密码，登入IDM后台管理平台.")
def login(request, params: LoginParams):
    admin_query = User.objects.filter(username=params.email)
    if admin_query.exists():
        if admin_query.filter(password=make_password(params.password)).exists():
            admin = admin_query.first()
            admin.token = admin.gen_token()
            return admin
        else:
            raise UserPasswordError()
    else:
        raise UserNotExist()
