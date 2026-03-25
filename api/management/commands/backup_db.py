import os
import time
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
from botocore.exceptions import NoCredentialsError

class Command(BaseCommand):
    help = 'Realiza o backup completo do banco de dados (Postgres/SQLite) e envia compactado para o AWS/Tigris S3 configurado'

    def handle(self, *args, **options):
        db_settings = settings.DATABASES['default']
        engine = db_settings.get('ENGINE')
        db_user = db_settings.get('USER')
        db_password = db_settings.get('PASSWORD')
        db_host = db_settings.get('HOST', 'localhost')
        db_port = str(db_settings.get('PORT', '5432'))
        db_name = db_settings.get('NAME')

        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        backup_filename = f'db_backup_{timestamp}.json.gz'
        backup_json_path = f'/tmp/db_backup_{timestamp}.json'
        backup_path = f'/tmp/{backup_filename}'

        # Dumping Django Database (Native Engine)
        self.stdout.write(f'Iniciando dump nativo do banco de dados (Cross-Platform)...')
        try:
            from django.core.management import call_command
            import gzip
            
            # Export via dumpdata
            with open(backup_json_path, 'w') as f:
                call_command('dumpdata', '--exclude', 'contenttypes', '--exclude', 'auth.Permission', stdout=f)
            
            # Compress to gzip
            with open(backup_json_path, 'rb') as f_in, gzip.open(backup_path, 'wb') as f_out:
                f_out.writelines(f_in)
                
            # Cleanup JSON temp
            os.remove(backup_json_path)
            self.stdout.write(self.style.SUCCESS(f'Backup serializado e compactado: {backup_path}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Falha ao gerar dump do Django: {e}'))
            return

        if not getattr(settings, 'AWS_ACCESS_KEY_ID', None):
            self.stdout.write(self.style.ERROR('Variável S3 AWS_ACCESS_KEY_ID não presente no ambiente. Upload cancelado, mas o arquivo local foi criado!'))
            return

        # S3 Upload Phase
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        self.stdout.write(f'Conectando com serviço S3...')
        
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=os.getenv('AWS_S3_REGION_NAME', 'auto'),
                endpoint_url=os.getenv('AWS_S3_ENDPOINT_URL')
            )
            
            s3_key = f'backups/{backup_filename}'
            
            self.stdout.write(f'Enviando /{s3_key} para o S3 ({bucket})...')
            s3_client.upload_file(backup_path, bucket, s3_key)
            self.stdout.write(self.style.SUCCESS(f'Sucesso! O Backup está seguro na Nuvem (Path: {s3_key})'))
            
            # Limpeza
            try:
                os.remove(backup_path)
                self.stdout.write('Arquivo temporário de dump apagado.')
            except OSError:
                pass
                
        except NoCredentialsError:
            self.stdout.write(self.style.ERROR('Credenciais AWS ausentes/inválidas no momento do upload.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro fatal durante integração S3 Tigris: {e}'))
