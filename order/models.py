from django.db import models


class OrderStatus(models.TextChoices):
    New = '未提交', '未提交'
    Submitted = '已提交', '已提交'


class Order(models.Model):
    order_num = models.CharField(max_length=128, verbose_name='流水号')
    author = models.CharField(max_length=128, verbose_name='著作权人')
    name = models.CharField(max_length=128, verbose_name='软著名称')
    agent = models.ForeignKey('agent.Agent', verbose_name='代理商', on_delete=models.CASCADE)
    work_time = models.IntegerField(verbose_name='工作日')
    pay_papers = models.BooleanField(verbose_name='是否写材料')

    status = models.CharField(max_length=10, verbose_name='单据状态', default=OrderStatus.New, choices=OrderStatus.choices)

    class Meta:
        verbose_name = '单据'
        verbose_name_plural = '单据'

    def __str__(self):
        return self.name
