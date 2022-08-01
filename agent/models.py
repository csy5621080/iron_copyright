from django.db import models


class Agent(models.Model):
    name = models.CharField(max_length=128, verbose_name='代理商名称')

    class Meta:
        verbose_name = '代理商'
        verbose_name_plural = '代理商'

    def __str__(self):
        return self.name
