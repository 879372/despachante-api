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
        backup_filename = f'db_backup_{timestamp}.sql.gz'
        backup_path = f'/tmp/{backup_filename}'

        if 'postgresql' in engine:
            if not db_name or not db_user:
                self.stdout.write(self.style.ERROR('As credenciais do Postgres não estão completas no ambiente.'))
                return

            self.stdout.write(f'Iniciando pg_dump para o host {db_host}...')
            
            os.environ['PGPASSWORD'] = str(db_password)
            command = [
                'pg_dump',
                '-h', db_host,
                '-p', db_port,
                '-U', db_user,
                '-Z', '9', # Gzip compression extra level
                '-f', backup_path,
                db_name
            ]
            
            try:
                subprocess.run(command, check=True)
                self.stdout.write(self.style.SUCCESS(f'Dump Postgres concluído: {backup_path}'))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f'Falha ao executar pg_dump: {e}'))
                return
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR('O aplicativo pg_dump não foi encontrado. Arquivo apt.txt com postgresql-client está ausente?'))
                return
                
        elif 'sqlite3' in engine:
            # Fallback para o modo de desenvolvimento local com SQLite local SQLite
            self.stdout.write(f'Iniciando backup local do arquivo SQLite...')
            db_path = str(db_name)
            if not os.path.exists(db_path):
                self.stdout.write(self.style.ERROR('Arquivo sqlite3 de origem não encontrado.'))
                return
                
            command = f'gzip -c "{db_path}" > "{backup_path}"'
            try:
                subprocess.run(command, shell=True, check=True)
                self.stdout.write(self.style.SUCCESS(f'Backup do SQLite concluído: {backup_path}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Falha ao comprimir sqlite3: {e}'))
                return
        else:
            self.stdout.write(self.style.ERROR('Mecanismo de banco de dados não suportado para o backup automático.'))
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
