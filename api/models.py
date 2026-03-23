from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nome")
    cpf_cnpj = models.CharField(max_length=20, verbose_name="CPF/CNPJ")
    phone = models.CharField(max_length=20, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.cpf_cnpj}"

class Process(models.Model):
    SERVICE_CHOICES = [
        ('Transferência', 'Transferência'),
        ('Licenciamento', 'Licenciamento'),
        ('Emplacamento', 'Emplacamento'),
        ('Segunda via', 'Segunda via'),
        ('Multa', 'Multa'),
        ('Outro', 'Outro'),
    ]
    
    STATUS_CHOICES = [
        ('Aberto', 'Aberto'),
        ('Em andamento', 'Em andamento'),
        ('Aguardando cliente', 'Aguardando cliente'),
        ('Finalizado', 'Finalizado'),
        ('Cancelado', 'Cancelado'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Pago', 'Pago'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="processes", verbose_name="Cliente")
    plate = models.CharField(max_length=10, verbose_name="Placa")
    renavam = models.CharField(max_length=20, blank=True, null=True, verbose_name="Renavam")
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES, verbose_name="Tipo de Serviço")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Aberto', verbose_name="Status")
    service_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Valor do Serviço")
    tax_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Valor das Taxas")
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True, verbose_name="Anexo")
    opened_at = models.DateField(verbose_name="Data de Abertura")
    due_date = models.DateField(blank=True, null=True, verbose_name="Data Prevista")
    finished_at = models.DateField(blank=True, null=True, verbose_name="Data de Conclusão")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    payment_method = models.CharField(max_length=50, blank=True, null=True, verbose_name="Forma de Pagamento")
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Pendente', verbose_name="Status de Pagamento")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.plate:
            self.plate = self.plate.upper().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.plate} - {self.service_type} ({self.client.name})"
