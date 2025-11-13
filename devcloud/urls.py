from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from cloud import views
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_user, name='register'),
    path('upload/', views.upload_file, name='upload_file'),
    path('download/<str:short_url>/', views.download_file, name='download'),
    path('file/<str:short_url>/', views.file_info, name='file_info'),
    path('category/create/', views.create_category, name='create_category'),  # ОДИН РАЗ
    path('file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('change-password/', views.change_password, name='change_password'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('file/<int:file_id>/detail/', views.file_detail, name='file_detail'),
    path('category/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('categories/', views.get_categories, name='get_categories'),
    
    # Редирект для стандартного маршрута Django
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('accounts/logout/', RedirectView.as_view(url='/logout/', permanent=False)),
]

# Обработчики ошибок
handler404 = 'cloud.views.custom_404'
handler500 = 'cloud.views.custom_500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)