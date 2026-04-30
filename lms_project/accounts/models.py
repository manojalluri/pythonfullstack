from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('instructor', 'Instructor'),
        ('student', 'Student'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Password Reset Fields
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_expiry = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_instructor(self):
        return self.role == 'instructor'
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    enrollment_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.student_id}"


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    instructor_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    qualification = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.instructor_id}"
