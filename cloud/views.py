import os
import json
import re  # Добавьте этот импорт
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.contrib.auth import login, authenticate, update_session_auth_hash  # Добавьте update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, Category, File, DownloadLog
from .forms import RegistrationForm, CategoryForm, FileUploadForm
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.db import models 
from django.db.models import Count
from django.http import Http404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username.lower(), password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'success': True, 'redirect_url': '/'})
            else:
                return JsonResponse({'error': 'Неверный логин или пароль'}, status=400)
        else:
            return JsonResponse({'error': 'Неверные данные'}, status=400)
    
    # Если GET запрос, показываем обычную страницу входа
    return render(request, 'cloud/login.html')

import os
import json
import re  # Добавьте этот импорт
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.contrib.auth import login, authenticate, update_session_auth_hash  # Добавьте update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, Category, File, DownloadLog
from .forms import RegistrationForm, CategoryForm, FileUploadForm
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.db import models 
from django.db.models import Count
from django.http import Http404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

# ... остальной код ...

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        user = request.user
        
        if not user.check_password(current_password):
            return JsonResponse({'error': 'Текущий пароль неверен'}, status=400)
        
        if new_password != confirm_password:
            return JsonResponse({'error': 'Пароли не совпадают'}, status=400)
        
        if len(new_password) < 8:
            return JsonResponse({'error': 'Пароль должен быть не менее 8 символов'}, status=400)
        
        user.set_password(new_password)
        user.save()
        
        # Обновляем аутентификацию пользователя
        update_session_auth_hash(request, user)  # Теперь эта функция доступна
        
        return JsonResponse({'success': True, 'message': 'Пароль успешно изменен'})
    
    return JsonResponse({'error': 'Неверный метод запроса'}, status=400)




def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').lower().strip()
        agree_terms = request.POST.get('agree_terms')
        
        # Валидация логина
        if not re.match(r'^[a-z0-9]+$', username):
            return JsonResponse({'error': 'Логин должен содержать только латинские буквы в нижнем регистре и цифры'}, status=400)
        
        if len(username) < 3:
            return JsonResponse({'error': 'Логин должен быть не менее 3 символов'}, status=400)
        
        if not agree_terms:
            return JsonResponse({'error': 'Необходимо согласие с условиями использования'}, status=400)
        
        # Проверка существования пользователя
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Пользователь с таким логином уже существует'}, status=400)
        
        # Проверка защиты от спама
        ip = get_client_ip(request)
        
        # Проверяем, была ли регистрация с этого IP за последние 10 минут
        recent_user = CustomUser.objects.filter(
            last_login_ip=ip,
            last_registration_attempt__gte=timezone.now() - timedelta(minutes=10)
        ).first()
        
        if recent_user:
            return JsonResponse({'error': 'Регистрация возможна только раз в 10 минут с одного устройства'}, status=400)
        
        # Генерируем случайный пароль
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        
        # Создаем пользователя
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            last_login_ip=ip,
            last_registration_attempt=timezone.now()
        )
        
        # Создаем стандартные категории
        Category.objects.create(user=user, name='Общее', color='#6366f1')
        Category.objects.create(user=user, name='Работа', color='#ef4444')
        Category.objects.create(user=user, name='Python', color='#3b82f6')
        
        # Автоматический вход
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'password': password,
            'message': f'Ваш временный пароль: {password}. Рекомендуем сменить его в настройках.'
        })
    
    return JsonResponse({'error': 'Неверные данные'}, status=400)

@login_required
def file_detail(request, file_id):
    """Получение детальной информации о файле для модального окна"""
    file = get_object_or_404(File, id=file_id, user=request.user)
    
    # Получаем логи скачивания
    download_logs = DownloadLog.objects.filter(file=file).order_by('-downloaded_at')[:10]
    
    # Формируем данные
    file_data = {
        'id': file.id,
        'original_name': file.original_name,
        'file_size': file.file_size,
        'file_type': file.file_type,
        'uploaded_at': file.uploaded_at.strftime('%d.%m.%Y %H:%M'),
        'expires_at': file.expires_at.strftime('%d.%m.%Y %H:%M'),
        'time_remaining': file.get_time_remaining(),
        'download_count': file.download_count,
        'short_url': file.short_url,
        'category': file.category.name if file.category else None,
    }
    
    logs_data = []
    for log in download_logs:
        logs_data.append({
            'time': log.downloaded_at.strftime('%d.%m.%Y %H:%M'),
            'ip_address': log.ip_address,
            'user_agent': log.user_agent,
            'download_speed': log.download_speed,
        })
    
    return JsonResponse({
        'file': file_data,
        'download_logs': logs_data
    })


@login_required
def dashboard(request):
    categories = Category.objects.filter(user=request.user)
    files = File.objects.filter(user=request.user).order_by('-uploaded_at')
    
    # Добавляем информацию о времени для каждого файла
    for file in files:
        file.time_remaining = file.get_time_remaining()
        file.is_forever = file.is_forever()  # Добавляем информацию о бессрочности
    
    # Вычисляем использованное место
    total_size = sum(f.file_size for f in files)
    storage_used = f"{total_size / (1024**3):.2f}"  # в GB
    
    # Вычисляем процент использования
    storage_percent = min(100, (total_size / (5 * 1024**3)) * 100)
    storage_percent = round(storage_percent, 1)
    
    # Удаляем просроченные файлы
    expired_files = File.objects.filter(user=request.user, expires_at__lt=timezone.now())
    for file in expired_files:
        if os.path.exists(file.file.path):
            os.remove(file.file.path)
        file.delete()
    
    return render(request, 'cloud/dashboard.html', {
        'categories': categories,
        'files': files,
        'storage_used': storage_used,
        'storage_percent': storage_percent
    })


def get_file_type(filename):
    ext = filename.split('.')[-1].lower()
    type_map = {
        'zip': 'archive', 'rar': 'archive', '7z': 'archive',
        'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 'svg': 'image', 'webp': 'image', 'bmp': 'image',
        'pdf': 'document',
        'py': 'code', 'js': 'code', 'html': 'code', 'css': 'code', 'php': 'code', 'java': 'code',
        'txt': 'text', 'doc': 'document', 'docx': 'document', 'rtf': 'document',
        # Видео форматы
        'mp4': 'video', 'avi': 'video', 'mov': 'video', 'wmv': 'video', 'flv': 'video', 
        'webm': 'video', 'mkv': 'video', 'm4v': 'video', '3gp': 'video', 'ogg': 'video',
        'mpg': 'video', 'mpeg': 'video', 'ts': 'video', 'mts': 'video', 'm2ts': 'video'
    }
    return type_map.get(ext, 'other')



@login_required
def upload_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = request.FILES['file']
            
            # Проверяем размер файла (5 ГБ)
            if file_obj.size > 5 * 1024 * 1024 * 1024:
                return JsonResponse({'error': 'Файл слишком большой. Максимальный размер 5 ГБ.'}, status=400)
            
            # Проверяем общий объем файлов пользователя
            total_size = sum(f.file_size for f in File.objects.filter(user=request.user))
            if total_size + file_obj.size > 5 * 1024 * 1024 * 1024:
                return JsonResponse({'error': 'Превышен лимит хранилища 5 ГБ.'}, status=400)
            
            file_instance = form.save(commit=False)
            file_instance.user = request.user
            file_instance.original_name = file_obj.name
            file_instance.file_size = file_obj.size
            file_instance.file_type = get_file_type(file_obj.name)
            
            # Обрабатываем категорию
            category_id = request.POST.get('category')
            if category_id:
                try:
                    category = Category.objects.get(id=category_id, user=request.user)
                    file_instance.category = category
                except Category.DoesNotExist:
                    pass
            
            # Обрабатываем время жизни
            lifetime = request.POST.get('lifetime', '24')
            if lifetime == 'forever' and request.user.is_superuser:
                # Для суперпользователя - бессрочное хранение (100 лет)
                file_instance.expires_at = timezone.now() + timedelta(days=365*100)
            else:
                try:
                    hours = int(lifetime)
                    file_instance.expires_at = timezone.now() + timedelta(hours=hours)
                except (ValueError, TypeError):
                    file_instance.expires_at = timezone.now() + timedelta(hours=24)
            
            file_instance.save()
            
            # Возвращаем информацию о том, бессрочный ли файл
            is_forever = lifetime == 'forever' and request.user.is_superuser
            
            return JsonResponse({
                'success': True,
                'file_id': file_instance.id,
                'short_url': file_instance.short_url,
                'is_forever': is_forever
            })
    
    return JsonResponse({'error': 'Ошибка загрузки'}, status=400)




def download_file(request, short_url):
    file_obj = get_object_or_404(File, short_url=short_url)
    
    if file_obj.is_expired():
        raise Http404("Файл больше не доступен")
    
    # Логируем скачивание
    DownloadLog.objects.create(
        file=file_obj,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    file_obj.download_count += 1
    file_obj.save()
    
    response = FileResponse(file_obj.file)
    response['Content-Disposition'] = f'attachment; filename="{file_obj.original_name}"'
    return response

def file_info(request, short_url):
    try:
        file_obj = File.objects.get(short_url=short_url)
        
        # Проверяем, не истёк ли файл
        if file_obj.is_expired():
            # Удаляем истёкший файл
            if os.path.exists(file_obj.file.path):
                os.remove(file_obj.file.path)
            file_obj.delete()
            raise Http404("Файл истёк")
        
        file_obj.time_remaining = file_obj.get_time_remaining()
        
        return render(request, 'cloud/file_info.html', {'file': file_obj})
        
    except File.DoesNotExist:
        # Файл не найден в базе
        return render(request, 'cloud/file_expired.html', status=404)
    

def custom_404(request, exception):
    """Кастомный обработчик 404 ошибок"""
    # Проверяем, является ли запрос к файлу
    if request.path.startswith('/file/') or request.path.startswith('/download/'):
        return render(request, 'cloud/file_expired.html', status=404)
    
    # Для других 404 ошибок используем стандартную страницу
    return render(request, 'cloud/404.html', status=404)  # Измените путь

def custom_500(request):
    """Кастомный обработчик 500 ошибок"""
    return render(request, 'cloud/500.html', status=500)  # Измените путь


# Вспомогательные функции
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_file_type(filename):
    # Приводим к нижнему регистру и разбиваем на части
    name_parts = filename.lower().split('.')
    if len(name_parts) < 2:
        return 'other'
    
    ext = name_parts[-1]
    print(f"Определение типа файла: {filename} -> расширение: {ext}")  # Для отладки
    
    type_map = {
        # Архивы
        'zip': 'archive', 'rar': 'archive', '7z': 'archive', 'tar': 'archive', 'gz': 'archive',
        
        # Изображения
        'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 
        'svg': 'image', 'webp': 'image', 'bmp': 'image', 'ico': 'image',
        
        # Видео (добавьте все нужные форматы)
        'mp4': 'video', 'avi': 'video', 'mov': 'video', 'wmv': 'video', 
        'flv': 'video', 'webm': 'video', 'mkv': 'video', 'm4v': 'video', 
        '3gp': 'video', 'ogg': 'video', 'mpg': 'video', 'mpeg': 'video',
        
        # Аудио (если нужно)
        'mp3': 'audio', 'wav': 'audio', 'ogg': 'audio', 'flac': 'audio',
        
        # Документы
        'pdf': 'document', 'doc': 'document', 'docx': 'document', 
        'rtf': 'document', 'txt': 'text', 'odt': 'document',
        
        # Код
        'py': 'code', 'js': 'code', 'html': 'code', 'css': 'code', 
        'php': 'code', 'java': 'code', 'cpp': 'code', 'c': 'code',
        'json': 'code', 'xml': 'code',
    }
    
    file_type = type_map.get(ext, 'other')
    print(f"Результат: {file_type}")  # Для отладки
    return file_type

def get_icon_class(file_type):
    icon_map = {
        'archive': 'bi-file-earmark-zip text-indigo-400',
        'image': 'bi-file-earmark-image text-pink-500', 
        'document': 'bi-file-earmark-pdf text-red-500',
        'code': 'bi-file-earmark-code text-green-500',
        'text': 'bi-file-earmark-text text-blue-500'
    }
    return icon_map.get(file_type, 'bi-file-earmark text-gray-400')




@require_POST
@login_required
def create_category(request):
    name = request.POST.get('name', '').strip()
    
    if not name:
        return JsonResponse({'error': 'Название категории не может быть пустым'}, status=400)
    
    # Более строгая проверка существования категории
    existing_category = Category.objects.filter(
        user=request.user, 
        name__iexact=name
    ).first()
    
    if existing_category:
        return JsonResponse({
            'success': True,  # Возвращаем success=True даже если категория существует
            'category': {
                'id': existing_category.id,
                'name': existing_category.name,
                'color': existing_category.color,
                'file_count': existing_category.file_set.count()
            }
        })
    
    try:
        # Автоматически назначаем цвет из предустановленных
        colors = ['#6366f1', '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
        existing_colors_count = Category.objects.filter(user=request.user).count()
        color = colors[existing_colors_count % len(colors)]
        
        category = Category.objects.create(
            user=request.user,
            name=name,
            color=color
        )
        
        return JsonResponse({
            'success': True, 
            'category': {
                'id': category.id,
                'name': category.name,
                'color': category.color,
                'file_count': 0
            }
        })
        
    except Exception as e:
        # Если произошла ошибка уникальности, все равно возвращаем успех
        # (скорее всего категория уже создана другим запросом)
        existing_category = Category.objects.filter(
            user=request.user, 
            name__iexact=name
        ).first()
        
        if existing_category:
            return JsonResponse({
                'success': True,
                'category': {
                    'id': existing_category.id,
                    'name': existing_category.name,
                    'color': existing_category.color,
                    'file_count': existing_category.file_set.count()
                }
            })
        
        return JsonResponse({'error': f'Ошибка при создании категории: {str(e)}'}, status=400)



@require_POST
@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    
    # Проверяем, есть ли файлы в категории
    if category.file_set.exists():
        return JsonResponse({
            'error': 'Невозможно удалить категорию, так как в ней есть файлы. Сначала переместите или удалите файлы.'
        }, status=400)
    
    category.delete()
    
    return JsonResponse({'success': True})

@login_required
def get_categories(request):
    """Получение списка категорий для AJAX"""
    categories = Category.objects.filter(user=request.user).annotate(
        file_count=Count('file')
    )
    
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'color': category.color,
            'file_count': category.file_count
        })
    
    return JsonResponse({'categories': categories_data})



@require_POST
@login_required
def delete_file(request, file_id):
    file = get_object_or_404(File, id=file_id, user=request.user)
    
    if os.path.exists(file.file.path):
        os.remove(file.file.path)
    
    file.delete()
    
    return JsonResponse({'success': True})

def file_info(request, short_url):
    file = get_object_or_404(File, short_url=short_url)
    
    if file.is_expired():
        return render(request, 'cloud/404.html', status=404)
    
    file.time_remaining = file.get_time_remaining()
    
    return render(request, 'cloud/file_info.html', {'file': file})

# Добавим метод в модель File для получения оставшегося времени
def get_time_remaining(self):
    from django.utils import timezone
    now = timezone.now()
    diff = self.expires_at - now
    
    if diff.total_seconds() <= 0:
        return "Истекло"
    
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    
    if hours > 0:
        return f"{hours} ч {minutes} мин"
    else:
        return f"{minutes} мин"

File.get_time_remaining = get_time_remaining
