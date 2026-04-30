from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    
    # Instructor URLs
    path('instructor/courses/', views.instructor_courses, name='instructor_courses'),
    path('instructor/create/', views.create_course, name='create_course'),
    path('instructor/edit/<int:course_id>/', views.edit_course, name='edit_course'),
    path('instructor/delete/<int:course_id>/', views.delete_course, name='delete_course'),
    path('instructor/<int:course_id>/add-lesson/', views.add_lesson, name='add_lesson'),
    path('instructor/lesson/edit/<int:lesson_id>/', views.edit_lesson, name='edit_lesson'),
    path('instructor/lesson/delete/<int:lesson_id>/', views.delete_lesson, name='delete_lesson'),
    path('instructor/lesson/<int:lesson_id>/add-material/', views.add_material, name='add_material'),
    path('instructor/material/delete/<int:material_id>/', views.delete_material, name='delete_material'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/courses/', views.manage_courses, name='manage_courses'),
]
