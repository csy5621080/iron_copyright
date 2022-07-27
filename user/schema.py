from ninja import Schema


class LoginParams(Schema):
    email: str
    password: str


class LoginResponse(Schema):
    id: int
    uuid: str
    name: str
    ceil_phone: str = None
    email: str = None
    token: str
