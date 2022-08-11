from ninja import NinjaAPI
from utils.authenticate import LoginChecker
from utils.tools import WCResponseRenderer
from django.conf import settings
# from user.views import user_api
from order.views import order_api
from utils.tools import BaseError
from jwt.exceptions import PyJWTError

api = NinjaAPI(auth=LoginChecker(), title="Windows Container Hub", renderer=WCResponseRenderer())

# 增加DEBUG验证, 非DEBUG环境, Api Docs隐藏.
if not settings.DEBUG:
    api.openapi_url = None

# api.add_router("/user/", user_api)
api.add_router("/order/", order_api)


@api.exception_handler(BaseError)
def handle_error(request, exc):
    request.failed = True
    return api.create_response(
        request,
        dict(
            code=exc.code,
            msg=exc.msg
        ),
        status=200
    )


@api.exception_handler(PyJWTError)
def handle_error(request, exc):
    request.failed = True
    return api.create_response(
        request,
        dict(
            code=17000,
            msg=exc.__str__()
        ),
        status=200
    )
