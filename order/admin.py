from django.contrib import admin
from .models import Order
from simpleui.admin import AjaxAdmin
import xlrd2 as xlrd
import os
import time
from django.conf import settings
from django.http import JsonResponse

# Register your models here.
admin.site.site_header = '小铁版权申报管理系统'  # 设置header
admin.site.site_title = '小铁版权申报管理系统'  # 设置title
admin.site.index_title = '小铁版权申报管理系统'


@admin.register(Order)
class OrderAdmin(AjaxAdmin):
    list_display = ('order_num', 'author', 'name', 'agent', 'work_time', 'pay_papers', 'status')
    actions = ['bulk_create']

    def bulk_create(self, request, queryset):
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
                setattr(tmp, cols_mapping[j], sheet1.cell(i, j).value)
            orders.append(tmp)
        Order.objects.bulk_create(orders)
        return JsonResponse(data={
            'status': 'success',
            'msg': '处理成功！'
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
