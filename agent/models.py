from django.db import models


class Agent(models.Model):
    name = models.CharField(max_length=128, verbose_name='代理商名称')
    suggested_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='建议价格', default='600.00')

    class Meta:
        verbose_name = '代理商'
        verbose_name_plural = '代理商'

    def __str__(self):
        return self.name
