from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-users/edit/<int:user_id>/', views.edit_user_admin, name='edit_user_admin'),
    path('manage-users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
]
