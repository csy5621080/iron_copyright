from django.contrib import admin
from .models import Order, OrderStatus, Cost, SubmittedOrder, UndeterminedOrder
from simpleui.admin import AjaxAdmin
import xlrd2 as xlrd
import os
import time
import xlwt
from django.conf import settings
from django.http import JsonResponse, FileResponse
from utils.logger import SysLogger
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.utils.html import format_html
from datetime import date, datetime
from django.db.models import ForeignKey

# Register your models here.

admin.site.site_header = '小铁版权申报管理系统'  # 设置header
admin.site.site_title = '小铁版权申报管理系统'  # 设置title
admin.site.index_title = '小铁版权申报管理系统'

ExcelColsMapping = {
    0: ("num", "do_pass", "序号"),
    1: ("delivery_date", date, "交件日期"),
    2: ("order_num", str, "流水号"),
    3: ("category", str, "变更|转让|查询|撤销|质权|补发"),
    4: ("registration_num", str, "登记号"),
    5: ("name", str, "软著名称"),
    6: ("author", str, "著作权人"),
    7: ("completion_date", date, "出证日期"),
    8: ("agent", ForeignKey, "代理商"),
    9: ("salesman", ForeignKey, "销售"),
    10: ("type", str, "业务类别"),
    11: ("offer_price", 'Decimal', "报价"),
    12: ("official_fees", 'Decimal', "官费"),
    13: ("cost", 'Decimal', "材料成本"),
    14: ("payment", str, "途径"),
    15: ("payment_date", date, "付款时间"),
    16: ("approval", bool, "款项审批"),
    17: ("profit", 'Decimal', "业绩"),
    18: ("is_completed", bool, "是否下证"),
    19: ("remarks", str, "备注"),
}


@admin.register(Cost)
class CostAdmin(AjaxAdmin):
    list_display = ('id', 'low', 'high', 'cost')
    ordering = ('id',)


@admin.register(Order)
class OrderAdmin(AjaxAdmin):
    list_display = ('id', 'order_num', 'author_display', 'name_display', 'agent', 'type', 'status',
                    'delivery_date', 'agreement_amount', 'completion_date',
                    'salesman', 'offer_price', 'official_fees', 'cost', 'payment', 'payment_date', 'profit', 'approval',
                    'is_completed')

    actions = ['bulk_create', 'submit', 'layer_input', 'approval']

    list_filter = ['agent']

    search_fields = ('order_num', 'name', 'agent__name')

    list_editable = ('agent', 'type', 'status',
                     'delivery_date', 'agreement_amount', 'completion_date',
                     'salesman', 'offer_price', 'official_fees', 'cost', 'payment', 'payment_date', 'profit',
                     'approval', 'is_completed')

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
        for i in range(0, int(len(order_nums) / 15)):
            order_num_list.append(order_nums[i * 15: (i + 1) * 15])
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

    @admin.display(description='著作权人', ordering='id')
    def author_display(self, obj):
        div = f'<div style="width:300px;min-width:250">{obj.author}</div>'
        return format_html(div)

    @admin.display(description='软著名称', ordering='id')
    def name_display(self, obj):
        div = f'<div style="width:300px;min-width:250">{obj.name}</div>'
        return format_html(div)

    @staticmethod
    def get_agent_id(agent_name):
        from agent.models import Agent
        agents = Agent.objects.filter(name=agent_name)
        if agents.exists():
            return agents.first().id
        else:
            return Agent.objects.create(name=agent_name).id

    @staticmethod
    def get_salesman_id(director_name):
        from director.models import Director
        directors = Director.objects.filter(name=director_name)
        if directors.exists():
            return directors.first().id
        else:
            return Director.objects.create(name=director_name, age=18).id

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
            if cols_num != 20:
                raise Exception('处理失败, 模板列数与要求不符，请检查模板.')
            for i in range(1, sheet1.nrows):
                tmp = Order()
                if len(sheet1.cell(i, 5).value) == 0 or len(sheet1.cell(i, 6).value) == 0:
                    continue
                for j in range(1, cols_num):
                    if ExcelColsMapping[j][1] == ForeignKey:
                        setattr(tmp, f'{ExcelColsMapping[j][0]}_id',
                                getattr(self, f'get_{ExcelColsMapping[j][0]}_id')(sheet1.cell(i, j).value))
                    elif ExcelColsMapping[j][1] == "do_pass":
                        pass
                    elif ExcelColsMapping[j][1] == date:
                        if sheet1.cell(i, j).value:
                            if sheet1.cell(i, j).ctype == 3:
                                date_value = xlrd.xldate_as_tuple(sheet1.cell_value(i, j), book.datemode)
                                time_obj = datetime.strptime(date(*date_value[:3]).strftime('%Y/%m/%d'), "%Y/%m/%d")
                            else:
                                time_obj = datetime.strptime(sheet1.cell(i, j).value, "%Y/%m/%d")
                            setattr(tmp, ExcelColsMapping[j][0], time_obj)
                        else:
                            setattr(tmp, ExcelColsMapping[j][0], None)
                    elif ExcelColsMapping[j][1] == bool:
                        is_ok = False
                        if sheet1.cell(i, j).value.lower() in ('ok', 'yes', 'true', '是', '是的', '已审批'):
                            is_ok = True
                        setattr(tmp, ExcelColsMapping[j][0], is_ok)
                    elif ExcelColsMapping[j][1] == 'Decimal':
                        decimal_value = sheet1.cell(i, j).value
                        if sheet1.cell(i, j).value == '':
                            decimal_value = 0
                        setattr(tmp, ExcelColsMapping[j][0], decimal_value)
                    else:
                        setattr(tmp, ExcelColsMapping[j][0], sheet1.cell(i, j).value)
                if not Order.objects.filter(order_num=tmp.order_num).exists():
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
            return JsonResponse(data={
                'status': 'failed',
                'msg': str(e)
            })

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
    list_display = ('id', 'order_num', 'author_display', 'name_display', 'agent', 'type', 'status',
                    'delivery_date', 'agreement_amount', 'completion_date',
                    'salesman', 'offer_price', 'official_fees', 'cost', 'payment', 'payment_date', 'profit', 'approval',
                    'is_completed')

    actions = ['submit']

    list_filter = ['agent']

    search_fields = ('order_num', 'name', 'agent__name')

    list_editable = ('agent', 'type',
                     'delivery_date', 'agreement_amount', 'completion_date',
                     'salesman', 'offer_price', 'official_fees', 'cost', 'payment', 'payment_date', 'profit',
                     'approval', 'is_completed')

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

    @admin.display(description='著作权人', ordering='id')
    def author_display(self, obj):
        div = f'<div style="width:300px;min-width:250">{obj.author}</div>'
        return format_html(div)

    @admin.display(description='软著名称', ordering='id')
    def name_display(self, obj):
        div = f'<div style="width:300px;min-width:250">{obj.name}</div>'
        return format_html(div)


@admin.register(SubmittedOrder)
class SubmittedOrderAdmin(AjaxAdmin):
    list_display = ('id', 'order_num', 'author_display', 'name_display', 'agent', 'type', 'status',
                    'delivery_date', 'agreement_amount', 'completion_date',
                    'salesman', 'offer_price', 'official_fees', 'cost', 'payment', 'payment_date', 'profit', 'approval',
                    'is_completed')

    list_filter = ['agent']

    actions = ['export', 'file_list']

    search_fields = ('order_num', 'name', 'agent__name')

    list_editable = ('agent', 'type',
                     'delivery_date', 'agreement_amount', 'completion_date',
                     'salesman', 'offer_price', 'official_fees', 'cost', 'payment', 'payment_date', 'profit',
                     'approval', 'is_completed')

    list_per_page = 25

    # download_uri = ''

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=OrderStatus.Submitted)

    @admin.display(description='著作权人', ordering='id')
    def author_display(self, obj):
        div = f'<div style="width:300px;min-width:250">{obj.author}</div>'
        return format_html(div)

    @admin.display(description='软著名称', ordering='id')
    def name_display(self, obj):
        div = f'<div style="width:300px;min-width:250">{obj.name}</div>'
        return format_html(div)

    def export(self, request, queryset):
        current_time = str(time.time())
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet('软件著作权')
        for i in range(0, 20):
            worksheet.write(0, i, ExcelColsMapping[i][2])
        for idx, obj in enumerate(queryset):
            for i in range(0, 20):
                if ExcelColsMapping[i][1] == "do_pass":
                    worksheet.write(idx + 1, i, "")
                elif ExcelColsMapping[i][1] == ForeignKey:
                    worksheet.write(idx + 1, i, getattr(getattr(obj, ExcelColsMapping[i][0]), "name"))
                elif ExcelColsMapping[i][1] == date:
                    time_str = ''
                    if getattr(obj, ExcelColsMapping[i][0], None):
                        time_str = datetime.strftime(getattr(obj, ExcelColsMapping[i][0]), "%Y/%m/%d")
                    worksheet.write(idx + 1, i, time_str)
                elif ExcelColsMapping[i][1] == bool:
                    if getattr(obj, ExcelColsMapping[i][0]):
                        worksheet.write(idx + 1, i, "是")
                    else:
                        worksheet.write(idx + 1, i, "否")
                else:
                    worksheet.write(idx + 1, i, getattr(obj, ExcelColsMapping[i][0]))
        workbook.save(f"./downloads/order_export_{current_time}.xlsx")
        # self.download_uri = f'{settings.SERVER_ADDR}/downloads/order_export_{current_time}.xlsx'
        response = FileResponse(open(f"./downloads/order_export_{current_time}.xlsx", 'rb'))
        response['content_type'] = "application/octet-stream"
        response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(
            f"./downloads/order_export_{current_time}.xlsx")
        return response

    export.short_description = '批量导出'
    export.type = 'success'
    export.icon = 'el-icon-download'

    def file_list(self, request, queryset):
        pass

    file_list.short_description = '已生成文件列表'
    file_list.icon = 'fas fa-audio-description'
    file_list.type = 'danger'
    file_list.style = 'color:black;'
    file_list.action_type = 1
    file_list.action_url = f'{settings.SERVER_ADDR}/downloads/'
