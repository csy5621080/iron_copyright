from django.contrib import admin
from .models import Order, OrderStatus, Cost, SubmittedOrder, UndeterminedOrder
from simpleui.admin import AjaxAdmin
import xlrd2 as xlrd
import os
import time
from django.conf import settings
from django.http import JsonResponse
from utils.logger import SysLogger
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.utils.html import format_html

# Register your models here.

admin.site.site_header = '小铁版权申报管理系统'  # 设置header
admin.site.site_title = '小铁版权申报管理系统'  # 设置title
admin.site.index_title = '小铁版权申报管理系统'


@admin.register(Cost)
class CostAdmin(AjaxAdmin):
    list_display = ('id', 'low', 'high', 'cost')
    ordering = ('id',)


@admin.register(Order)
class OrderAdmin(AjaxAdmin):
    list_display = ('id', 'order_num', 'author_display', 'name_display', 'agent', 'work_time', 'pay_papers', 'status',
                    'delivery_date', 'agreement_amount', 'completion_date',
                    'salesman', 'offer_price', 'cost', 'payment', 'payment_date', 'profit', 'approval', 'is_completed')

    actions = ['bulk_create', 'submit', 'layer_input', 'approval']

    list_filter = ['agent']

    search_fields = ('order_num', 'name', 'agent__name')

    list_editable = ('agent', 'work_time', 'pay_papers', 'status',
                     'delivery_date', 'agreement_amount', 'completion_date',
                     'salesman', 'offer_price', 'cost', 'payment', 'payment_date', 'profit', 'approval', 'is_completed')

    list_per_page = 25

    def layer_input(self, request, queryset):
        # 这里的queryset 会有数据过滤，只包含选中的数据

        post = request.POST
        # 这里获取到数据后，可以做些业务处理
        # post中的_action 是方法名
        # post中 _selected 是选中的数据，逗号分割
        print(request)
        order_nums = post.get('order_nums')
        order_nums = order_nums.replace(' ', '')
        if len(order_nums) % 15:
            return JsonResponse(data={
                'status': 'error',
                'msg': '长度没有被15整除哟~是不是有输入错误呀~'
            })
        order_num_list = []
        for i in range(0, int(len(order_nums)/15)):
            order_num_list.append(order_nums[i*15: (i+1)*15])
        Order.objects.filter(order_num__in=order_num_list).update(status=OrderStatus.Undetermined)
        return JsonResponse(data={
            'status': 'success',
            'msg': '处理成功！'
        })

    layer_input.short_description = '批量待定'
    layer_input.type = 'success'
    layer_input.icon = 'el-icon-s-promotion'

    # 指定一个输入参数，应该是一个数组

    # 指定为弹出层，这个参数最关键
    layer_input.layer = {
        # 弹出层中的输入框配置

        # 这里指定对话框的标题
        'title': '批量待定',
        # 提示信息
        'tips': '应杨小铁产品同志的强烈要求，增加这个玩意儿。',
        # 确认按钮显示文本
        'confirm_button': '确认提交',
        # 取消按钮显示文本
        'cancel_button': '取消',

        # 弹出层对话框的宽度，默认50%
        'width': '40%',

        # 表单中 label的宽度，对应element-ui的 label-width，默认80px
        'labelWidth': "80px",
        'params': [{
            # 这里的type 对应el-input的原生input属性，默认为input
            'type': 'textarea',
            # key 对应post参数中的key
            'key': 'order_nums',
            # 显示的文本
            'label': '流水号',
            # 为空校验，默认为False
            'require': True
        }]
    }

    def submit(self, request, queryset):
        queryset.update(status=OrderStatus.Submitted)
        messages.add_message(request, messages.SUCCESS, '提交成功')

    submit.short_description = '提交'
    submit.type = 'success'
    submit.icon = 'fas fa-audio-description'
    submit.enable = True

    @admin.display(description='成本', ordering='id')
    def cost(self, obj):
        cost = Cost.objects.filter(low__lt=obj.work_time, high__gte=obj.work_time)
        if cost.exists():
            cost = cost.first().cost
        else:
            cost = 0
        div = f'<div style = "display: table-cell;vertical-align: middle;text-align:center;" >{cost}</div>'
        return mark_safe(div)

    @admin.display(description='著作权人', ordering='id')
    def author_display(self, obj):
        div = f'<div style="min-width: 350px">{obj.author}</div>'
        return format_html(div)

    @admin.display(description='软著名称', ordering='id')
    def name_display(self, obj):
        div = f'<div style="min-width: 350px">{obj.name}</div>'
        return format_html(div)

    @staticmethod
    def get_agent_id(agent_name):
        from agent.models import Agent
        agents = Agent.objects.filter(name=agent_name)
        if agents.exists():
            return agents.first().id
        else:
            return Agent.objects.create(name=agent_name).id

    def approval(self, request, queryset):
        queryset.update(approval=True)
        messages.add_message(request, messages.SUCCESS, '审批成功')

    approval.short_description = '批量审批'
    approval.type = 'success'
    approval.icon = 'el-icon-s-promotion'
    approval.enable = True
    approval.confirm = '你确定要审批选中单据吗？'

    def bulk_create(self, request, queryset):
        try:
            file_obj = request.FILES['upload']
            current_time = str(time.time())
            file_path = os.path.join(settings.FILES_ROOT, current_time + file_obj.name)
            file = open(file_path, 'wb')
            for chunk in file_obj.chunks():
                file.write(chunk)
            file.close()
            book = xlrd.open_workbook(file_path)
            sheet1 = book.sheets()[0]
            orders = []
            cols_num = sheet1.ncols
            if cols_num != 6:
                raise Exception('模板格式有误')
            cols_mapping = {
                0: "order_num",
                1: "author",
                2: "name",
                3: "agent",
                4: "work_time",
                5: "pay_papers",
            }
            for i in range(1, sheet1.nrows):
                tmp = Order()
                for j in range(cols_num):
                    if j == 3:
                        setattr(tmp, 'agent_id', self.get_agent_id(sheet1.cell(i, j).value))
                    else:
                        setattr(tmp, cols_mapping[j], sheet1.cell(i, j).value)
                orders.append(tmp)
            Order.objects.bulk_create(orders)
            if os.path.exists(file_path):
                os.remove(file_path)
            return JsonResponse(data={
                'status': 'success',
                'msg': '处理成功！'
            })
        except Exception as e:
            SysLogger.exception(e)
            raise e

    bulk_create.short_description = '批量导入'
    bulk_create.type = 'success'
    bulk_create.icon = 'el-icon-upload'
    bulk_create.enable = True

    bulk_create.layer = {
        'params': [{
            'type': 'file',
            'key': 'upload',
            'label': '文件'
        }]
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=OrderStatus.New)


@admin.register(UndeterminedOrder)
class UndeterminedOrderAdmin(AjaxAdmin):
    list_display = ('id', 'order_num', 'author', 'name', 'agent', 'work_time', 'pay_papers', 'status',
                    'delivery_date', 'agreement_amount', 'completion_date',
                    'salesman', 'offer_price', 'cost', 'payment', 'payment_date', 'profit', 'approval', 'is_completed')

    actions = ['submit']

    list_filter = ['agent']

    search_fields = ('order_num', 'name', 'agent__name')

    list_editable = ('agent', 'work_time', 'pay_papers',
                     'delivery_date','agreement_amount', 'completion_date',
                     'salesman', 'offer_price', 'cost', 'payment', 'payment_date', 'profit', 'approval', 'is_completed')

    list_per_page = 25

    def submit(self, request, queryset):
        queryset.update(status=OrderStatus.Submitted)

    submit.short_description = '提交'
    submit.type = 'success'
    submit.icon = 'fas fa-audio-description'
    submit.enable = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=OrderStatus.Undetermined)


@admin.register(SubmittedOrder)
class SubmittedOrderAdmin(AjaxAdmin):
    list_display = ('id', 'order_num', 'author', 'name', 'agent', 'work_time', 'pay_papers', 'status',
                    'delivery_date', 'agreement_amount', 'completion_date',
                    'salesman', 'offer_price', 'cost', 'payment', 'payment_date', 'profit', 'approval', 'is_completed')

    list_filter = ['agent']

    search_fields = ('order_num', 'name', 'agent__name')

    list_editable = ('agent', 'work_time', 'pay_papers',
                     'delivery_date', 'agreement_amount', 'completion_date',
                     'salesman', 'offer_price', 'cost', 'payment', 'payment_date', 'profit', 'approval', 'is_completed')

    list_per_page = 25

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=OrderStatus.Submitted)

    @admin.display(description='著作权人', ordering='name')
    def name(self, obj):
        div = f"<img src='{obj.name}' min-width='300px' width='500px'>"
        return mark_safe(div)
