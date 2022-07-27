import jwt
import time
from jwt.exceptions import PyJWTError


class JWTToken(object):

    def __init__(self, exp: int = 7200):
        self.salt = 'idm_admin'  # settings.SALT
        self.exp = exp
        self.algorithm = 'HS256'

    def encode(self, payload: dict):
        payload['exp'] = time.time() + self.exp
        return jwt.encode(payload, self.salt, algorithm=self.algorithm)

    def decode(self, token):
        try:
            payload = jwt.decode(token, self.salt, algorithms=[self.algorithm])
            return payload
        except PyJWTError as e:
            raise e


