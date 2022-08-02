from django.db import models


class Director(models.Model):
    name = models.CharField(max_length=128, verbose_name='经理姓名')
    age = models.IntegerField(verbose_name='年龄')

    class Meta:
        verbose_name = '经理'
        verbose_name_plural = '经理'

    def __str__(self):
        return self.name
