from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
    path('create-task/', views.create_task, name='create_task'),
    path('update-task/<int:pk>/', views.update_task, name='update_task'),
    path('delete-task/<int:pk>/', views.delete_task, name='delete_task'),
    path('toggle-task/<int:pk>/', views.toggle_task, name='toggle_task'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('health-metrics/', views.health_metrics, name='health_metrics'),
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
    path('ai-response/', views.ai_response, name='ai_response'),
    path('trigger-sos/', views.trigger_sos, name='trigger_sos'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('health-data/', views.health_data_api, name='health_data_api'),
    path('family-sync/', views.manage_family, name='manage_family'),
    path('image-analysis/', views.medical_image_analysis, name='image_analysis'),
    path('diet-plans/', views.diet_plans, name='diet_plans'),
    path('', views.landing, name='home'),
]
