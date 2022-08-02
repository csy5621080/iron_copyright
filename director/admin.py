from django.contrib import admin
from simpleui.admin import AjaxAdmin
from .models import Director


@admin.register(Director)
class DirectorAdmin(AjaxAdmin):
    list_display = ('id', 'name', 'age')

