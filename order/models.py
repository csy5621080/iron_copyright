from django.db import models


class OrderStatus(models.TextChoices):
    New = '未提交', '未提交'
    Submitted = '已提交', '已提交'
    Undetermined = '待定', '待定'


class OrderCategory(models.TextChoices):
    Alteration = '变更', '变更'
    Make_over = '转让', '转让'
    query = '查询', '查询'
    cancel = '撤销', '撤销'
    pledge = '质权', '质权'
    reissue = '补发', '补发'


class OrderPayment(models.TextChoices):
    Wechat = '微信', '微信'
    CorpRemittance = '对公', '对公'


class Order(models.Model):
    order_num = models.CharField(max_length=128, verbose_name='流水号')
    author = models.CharField(max_length=128, verbose_name='著作权人')
    name = models.CharField(max_length=128, verbose_name='软著名称')
    agent = models.ForeignKey('agent.Agent', verbose_name='代理商', on_delete=models.CASCADE)
    work_time = models.IntegerField(verbose_name='工作日')
    pay_papers = models.BooleanField(verbose_name='是否写材料')

    delivery_date = models.DateField(verbose_name='交件日期', null=True, blank=True)
    category = models.CharField(max_length=36, verbose_name='业务类别', null=True, blank=True,
                                choices=OrderCategory.choices)
    registration_num = models.CharField(max_length=128, verbose_name='登记号', null=True, blank=True)

    agreement_amount = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='协议金额', null=True, blank=True,
                                           default=0)

    completion_date = models.DateField(verbose_name='出证日期', null=True, blank=True)
    salesman = models.ForeignKey('director.Director', verbose_name='销售', on_delete=models.CASCADE, null=True, blank=True)

    offer_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='报价', null=True, blank=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='成本', null=True, blank=True)

    payment = models.CharField(max_length=128, choices=OrderPayment.choices, null=True, blank=True, verbose_name='付款途径')
    payment_date = models.DateField(null=True, blank=True, verbose_name='付款时间')

    profit = models.DecimalField(default=0, max_digits=8, decimal_places=2, verbose_name='利润')

    approval = models.BooleanField(default=False, verbose_name='款项审批')

    is_completed = models.BooleanField(default=False, verbose_name='是否下证')

    status = models.CharField(max_length=10, verbose_name='单据状态', default=OrderStatus.New, choices=OrderStatus.choices)

    remarks = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '单据'
        verbose_name_plural = '单据'

    def __str__(self):
        return self.name


class UndeterminedOrder(Order):
    class Meta:
        verbose_name = "待定单据"
        verbose_name_plural = verbose_name
        proxy = True


class SubmittedOrder(Order):
    class Meta:
        verbose_name = "已提交单据"
        verbose_name_plural = verbose_name
        proxy = True


class Cost(models.Model):
    low = models.IntegerField(default=0, verbose_name='最低工作日')
    high = models.IntegerField(default=1000, verbose_name='最高工作日')
    cost = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='成本')

    class Meta:
        verbose_name = '成本'
        verbose_name_plural = '成本'
