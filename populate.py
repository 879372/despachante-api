import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Client, Process
from django.contrib.auth.models import User

def run():
    print("🧹 Limpando dados antigos...")
    Client.objects.all().delete()
    Process.objects.all().delete()

    print("👤 Criando clientes...")
    c1 = Client.objects.create(name='João Silva', cpf_cnpj='12345678901', phone='11999999999', email='joao@exemplo.com')
    c2 = Client.objects.create(name='Maria Transportes LTDA', cpf_cnpj='12345678000199', phone='11888888888', email='contato@mariatransportes.com')
    c3 = Client.objects.create(name='Carlos Pereira', cpf_cnpj='98765432100', phone='21977777777', email='carlos@exemplo.com')

    print("📄 Criando processos...")
    processes_data = [
        (c1, 'ABC1234', '12345678901', 'Transferência', 'Em andamento', 350.50, date.today() - timedelta(days=5), None, 'Pendente'),
        (c1, 'XYZ9876', '98765432109', 'Licenciamento', 'Finalizado', 180.00, date.today() - timedelta(days=30), date.today() - timedelta(days=2), 'Pago'),
        (c2, 'FHH8888', '11122233344', 'Emplacamento', 'Aberto', 500.00, date.today() - timedelta(days=1), None, 'Pendente'),
        (c3, 'LLL1111', '55566677788', 'Segunda via', 'Aguardando cliente', 120.00, date.today() - timedelta(days=15), None, 'Pendente'),
        (c2, 'DEF5678', '44455566677', 'Transferência', 'Finalizado', 450.00, date.today() - timedelta(days=40), date.today() - timedelta(days=10), 'Pago'),
    ]

    for p in processes_data:
        Process.objects.create(
            client=p[0], plate=p[1], renavam=p[2], service_type=p[3], 
            status=p[4], value=p[5], opened_at=p[6], finished_at=p[7], payment_status=p[8]
        )
        
    print("🔑 Criando usuário admin (admin/admin)...")
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')

    print("✅ Banco populado com sucesso!")

if __name__ == '__main__':
    run()
