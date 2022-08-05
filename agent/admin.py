from django.contrib import admin
from simpleui.admin import AjaxAdmin
from .models import Agent


@admin.register(Agent)
class AgentAdmin(AjaxAdmin):
    list_display = ('id', 'name', 'suggested_price')
