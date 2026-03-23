from rest_framework import viewsets, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F, Count
from rest_framework.pagination import PageNumberPagination
from .models import Client, Process
from .serializers import ClientSerializer, ProcessSerializer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10000

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get('paginate') == 'false':
            return None
        return super().paginate_queryset(queryset, request, view=view)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all().order_by('-created_at')
    serializer_class = ClientSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    pagination_class = StandardResultsSetPagination
    search_fields = ['name', 'cpf_cnpj', 'phone', 'email']
    ordering_fields = ['created_at', 'name']

from django_filters import rest_framework as django_filters

class ProcessFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="opened_at", lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name="opened_at", lookup_expr='lte')

    class Meta:
        model = Process
        fields = ['client', 'plate', 'status', 'service_type', 'payment_status']

class ProcessViewSet(viewsets.ModelViewSet):
    queryset = Process.objects.select_related('client').all().order_by('-created_at')
    serializer_class = ProcessSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    pagination_class = StandardResultsSetPagination
    filterset_class = ProcessFilter
    ordering_fields = ['opened_at', 'created_at', 'service_value', 'tax_value']
    search_fields = ['plate', 'renavam', 'client__name']

from django.db.models.functions import TruncMonth

class DashboardViewSet(viewsets.ViewSet):
    def list(self, request):
        client_id = request.query_params.get('client_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        processes = Process.objects.all()

        if client_id:
            processes = processes.filter(client_id=client_id)
        if start_date:
            processes = processes.filter(opened_at__gte=start_date)
        if end_date:
            processes = processes.filter(opened_at__lte=end_date)

        total_processes = processes.count()
        in_progress_processes = processes.filter(status__in=['Aberto', 'Em andamento', 'Aguardando cliente']).count()
        finished_processes = processes.filter(status='Finalizado').count()
        
        # O dashboard só contabiliza o service_value quando pago
        total_value = processes.filter(payment_status='Pago').aggregate(total=Sum('service_value'))['total'] or 0

        # Graficos
        monthly_data_qs = processes.annotate(month=TruncMonth('opened_at')).values('month', 'payment_status').annotate(
            qtd=Count('id'),
            valor=Sum('service_value')
        ).order_by('month')
        
        months = {}
        for item in monthly_data_qs:
            if not item['month']: continue
            month_str = item['month'].strftime('%m/%Y')
            if month_str not in months:
                months[month_str] = {'name': month_str, 'pago_qtd': 0, 'pago_valor': 0, 'pendente_qtd': 0, 'pendente_valor': 0}
            
            status_prefix = 'pago' if item['payment_status'] == 'Pago' else 'pendente'
            months[month_str][f"{status_prefix}_qtd"] += item['qtd']
            months[month_str][f"{status_prefix}_valor"] += float(item['valor'] or 0)
            
        bar_chart_data = list(months.values())

        client_qs = processes.values('client__name').annotate(qtd=Count('id'), valor=Sum('service_value')).order_by('-qtd')[:4]
        pie_chart_data = [{'name': s['client__name'], 'value': s['qtd'], 'amount': float(s['valor'] or 0)} for s in client_qs]

        return Response({
            'total_processes': total_processes,
            'in_progress_processes': in_progress_processes,
            'finished_processes': finished_processes,
            'total_value': total_value,
            'bar_chart_data': bar_chart_data,
            'pie_chart_data': pie_chart_data
        })
