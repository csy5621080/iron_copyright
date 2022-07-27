import hashlib
import orjson
import string
import random
from typing import Any
from django.http import HttpRequest
from ninja.renderers import BaseRenderer


class NoError(object):

    def __init__(self):
        self.code = 0
        self.msg = "成功"


def make_password(pwd):
    s = hashlib.sha256()
    s.update(pwd.encode())
    hash_pwd = s.hexdigest()
    return hash_pwd


class BaseError(Exception):

    def __init__(self):
        pass


class WCResponseRenderer(BaseRenderer):
    media_type = "application/json"

    def render(self, request: HttpRequest, data: Any, *, response_status: int) -> Any:
        if getattr(request, 'failed', False):
            return orjson.dumps(data)
        return orjson.dumps(dict(code=0, msg='SUCCESS', data=data))


def get_image_path(instance, filename):
    module_name = instance.__class__.__name__.lower()
    suffix = filename.split(".")[-1]

    if module_name == 'user':
        return f'WCHub/user_avatar/{instance.uuid}.{suffix}'
    elif module_name == 'image':
        return f'WCHub/repo_icon/{instance.name}.{suffix}'


def gen_random_str(length, sign=False):
    if sign:
        scope = string.ascii_letters + string.digits + r"""!#$%&()*+,-./:;<=>?@[]^_`{|}~"""  # 去掉 \ ' "
    else:
        scope = string.ascii_letters + string.digits
    return ''.join(random.sample(scope, length))
