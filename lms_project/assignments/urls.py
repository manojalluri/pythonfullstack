from django.urls import path
from . import views

urlpatterns = [
    # Student URLs
    path('my-assignments/', views.my_assignments, name='my_assignments'),
    path('submit/<int:assignment_id>/', views.submit_assignment, name='submit_assignment'),
    path('my-grades/', views.my_grades, name='my_grades'),
    
    # Instructor URLs
    path('instructor/assignments/', views.instructor_assignments, name='instructor_assignments'),
    path('instructor/create/', views.create_assignment, name='create_assignment'),
    path('instructor/edit/<int:assignment_id>/', views.edit_assignment, name='edit_assignment'),
    path('instructor/delete/<int:assignment_id>/', views.delete_assignment, name='delete_assignment'),
    path('instructor/submissions/', views.submissions_pending, name='submissions_pending'),
    path('instructor/grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),
    
    # Shared
    path('<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
]
