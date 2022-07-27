import uuid
from django.db import models
from utils.token import JWTToken
from django.conf import settings
from django.core.cache import cache


class User(models.Model):
    uuid = models.CharField(max_length=32, unique=True, null=False)
    name = models.CharField(max_length=128)
    email = models.CharField(max_length=128)
    ceil_phone = models.CharField(max_length=128)
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'wc_user'

    def gen_token(self):
        token = JWTToken(settings.SIGN_IN_TIMEOUT).encode(dict(id=self.id, uuid=self.uuid))
        cache.set(f'admin_{self.uuid}', token, timeout=settings.SIGN_IN_TIMEOUT)
        return token

    def logout(self):
        cache.delete(f'admin_{self.uuid}')

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = uuid.uuid4().hex
        super(User, self).save(*args, **kwargs)


class Computer(models.Model):
    device_name = models.CharField(max_length=256, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.device_name

    class Meta:
        db_table = 'user_computer'
        verbose_name = '用户设备'
        verbose_name_plural = verbose_name
