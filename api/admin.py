from django.contrib import admin
from .models import Client, Process

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpf_cnpj', 'phone', 'created_at')
    search_fields = ('name', 'cpf_cnpj')

@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ('plate', 'client', 'service_type', 'status', 'service_value', 'tax_value', 'payment_status', 'opened_at')
    list_filter = ('status', 'payment_status', 'service_type')
    search_fields = ('plate', 'renavam', 'client__name')
