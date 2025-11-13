from django.core.management.base import BaseCommand
from django.utils import timezone
from cloud.models import File
import os

class Command(BaseCommand):
    help = 'Удаляет просроченные файлы'
    
    def handle(self, *args, **options):
        expired_files = File.objects.filter(expires_at__lt=timezone.now())
        count = 0
        
        for file in expired_files:
            if os.path.exists(file.file.path):
                os.remove(file.file.path)
            file.delete()
            count += 1
        
        self.stdout.write(f'Удалено {count} просроченных файлов')