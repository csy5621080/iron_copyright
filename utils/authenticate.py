from typing import Optional, Any
from django.http import HttpRequest
from utils.token import JWTToken
from user.models import User
from django.core.cache import cache
from django.conf import settings
from jwt.exceptions import ExpiredSignatureError
from utils.logger import SysLogger
from user.exceptions import UserNotLogin, UserNotExist
from ninja.security import APIKeyHeader


def parse_token(token):
    try:
        payload = JWTToken().decode(token)
        admin_query = User.objects.filter(id=payload['id'])
        if not cache.get(f"admin_{payload['uuid']}"):
            raise UserNotLogin()
        if admin_query.exists():
            cache.set(f"admin_{payload['uuid']}", token, timeout=settings.SIGN_IN_TIMEOUT)
            return admin_query.first()
        else:
            raise UserNotExist()
    except ExpiredSignatureError as e:
        SysLogger.exception('ExpiredSignatureError,', e)
        raise e
    except Exception as e:
        SysLogger.exception('parse token error,', e)
        raise e


class LoginChecker(APIKeyHeader):
    param_name = "Auth-Token"

    def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
        administrator = parse_token(token)
        request.admin = administrator
        return token
