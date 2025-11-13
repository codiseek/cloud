import os
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True, verbose_name='Логин')
    password = models.CharField(max_length=128, verbose_name='Пароль')
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_registration_attempt = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Приводим логин к нижнему регистру
        self.username = self.username.lower()
        super().save(*args, **kwargs)

class Category(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#6366f1')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def save(self, *args, **kwargs):
        # Нормализуем имя перед сохранением
        self.name = self.name.strip()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    

def user_directory_path(instance, filename):
    # Файлы сохраняем в: protected_uploads/user_id/unique_folder/filename
    return f'protected_uploads/{instance.user.id}/{instance.unique_folder}/{filename}'

class File(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to=user_directory_path)
    file_size = models.BigIntegerField()  # в байтах
    file_type = models.CharField(max_length=50)
    unique_folder = models.UUIDField(default=uuid.uuid4, unique=True)
    short_url = models.CharField(max_length=10, unique=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    download_count = models.IntegerField(default=0)
    
    def is_forever(self):
        """Проверяет, является ли файл бессрочным"""
        # Считаем файл бессрочным, если срок жизни больше 50 лет
        return self.expires_at > timezone.now() + timedelta(days=50*365)
    
    def save(self, *args, **kwargs):
        if not self.short_url:
            self.short_url = self.generate_short_url()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def generate_short_url(self):
        import random
        import string
        chars = string.ascii_letters + string.digits
        while True:
            short_url = ''.join(random.choices(chars, k=5))
            if not File.objects.filter(short_url=short_url).exists():
                return short_url
    
    def is_expired(self):
        return timezone.now() > self.expires_at

class DownloadLog(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    download_speed = models.FloatField(null=True, blank=True)  # MB/s
    
    def get_browser(self):
        ua = self.user_agent.lower()
        if 'chrome' in ua and 'edg' not in ua:
            return 'Chrome'
        elif 'firefox' in ua:
            return 'Firefox'
        elif 'safari' in ua and 'chrome' not in ua:
            return 'Safari'
        elif 'edg' in ua:
            return 'Edge'
        else:
            return 'Other'
    
    def get_platform(self):
        ua = self.user_agent.lower()
        if 'windows' in ua:
            return 'Windows'
        elif 'mac' in ua:
            return 'macOS'
        elif 'linux' in ua:
            return 'Linux'
        elif 'android' in ua:
            return 'Android'
        elif 'ios' in ua:
            return 'iOS'
        else:
            return 'Unknown'