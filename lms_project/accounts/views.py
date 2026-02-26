from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
import uuid
from .models import User, StudentProfile, InstructorProfile
from courses.models import Course, Enrollment
from assignments.models import Assignment, Submission, Grade


def home(request):
    featured_courses = Course.objects.filter(status='published')[:6]
    return render(request, 'home.html', {'featured_courses': featured_courses})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role', 'student')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'accounts/register.html')
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=first_name,
                    last_name=last_name,
                    role=role
                )
                
                # Create profile based on role
                if role == 'student':
                    student_id = f"STU{user.id:05d}"
                    StudentProfile.objects.create(user=user, student_id=student_id)
                elif role == 'instructor':
                    instructor_id = f"INS{user.id:05d}"
                    InstructorProfile.objects.create(user=user, instructor_id=instructor_id)
                
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'accounts/register.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard(request):
    user = request.user
    context = {}
    
    if user.is_student():
        enrollments = Enrollment.objects.filter(student=user).select_related('course', 'course__instructor')
        context['enrolled_courses_count'] = enrollments.count()
        # Map enrollments to a common course structure
        context['recent_courses'] = [
            {
                'id': e.course.id,
                'title': e.course.title,
                'instructor_name': e.course.instructor.get_full_name() or e.course.instructor.username,
                'status': e.status,
                'progress': e.progress,
                'is_enrollment': True
            } for e in enrollments[:5]
        ]
        
        # Get assignment stats
        submissions = Submission.objects.filter(student=user)
        context['completed_assignments'] = submissions.filter(status='graded').count()
        context['pending_assignments'] = submissions.filter(status='submitted').count()
        
        # Get average grade
        grades = Grade.objects.filter(submission__student=user)
        if grades.exists():
            grade_list = [g.percentage() for g in grades if g.score is not None]
            if grade_list:
                context['average_grade'] = round(sum(grade_list) / len(grade_list), 1)
        
        context['recent_activity'] = [
            {'title': 'New Course Available', 'description': 'Check out the new Data Science course!'},
            {'title': 'Assignment Due', 'description': 'Your Python project is due in 3 days.'}
        ]
        
    elif user.is_instructor():
        courses = Course.objects.filter(instructor=user)
        context['courses_count'] = courses.count()
        context['recent_courses'] = [
            {
                'id': c.id,
                'title': c.title,
                'instructor_name': user.get_full_name() or user.username,
                'status': c.status,
                'progress': 100 if c.status == 'published' else 0,
                'is_enrollment': False
            } for c in courses[:5]
        ]
        
        total_students = Enrollment.objects.filter(course__instructor=user).values('student').distinct().count()
        context['total_students'] = total_students
        
        assignments = Assignment.objects.filter(course__instructor=user)
        context['assignments_count'] = assignments.count()
        
        pending = Submission.objects.filter(assignment__course__instructor=user, status='submitted').count()
        context['pending_submissions'] = pending
        
        context['recent_activity'] = [
            {'title': 'New Submission', 'description': 'Alice Walker submitted "First Project".'},
            {'title': 'Course Enrollment', 'description': 'Bob Miller enrolled in your Web Bootcamp.'}
        ]
        
    else:  # Admin
        context['total_users'] = User.objects.count()
        context['total_courses'] = Course.objects.count()
        context['total_instructors'] = User.objects.filter(role='instructor').count()
        context['total_students'] = User.objects.filter(role='student').count()
        
        recent_courses = Course.objects.all().select_related('instructor')[:5]
        context['recent_courses'] = [
            {
                'id': c.id,
                'title': c.title,
                'instructor_name': c.instructor.get_full_name() or c.instructor.username,
                'status': c.status,
                'progress': 100 if c.status == 'published' else 0,
                'is_enrollment': False
            } for c in recent_courses
        ]
        
        context['recent_activity'] = [
            {'title': 'System Health', 'description': 'All systems are running optimally.'},
            {'title': 'Security Audit', 'description': 'A successful security scan was completed today.'}
        ]
    
    return render(request, 'dashboard.html', context)


@login_required
def manage_users(request):
    if not request.user.is_admin():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    users = User.objects.all().order_by('-created_at')
    return render(request, 'accounts/manage_users.html', {'users': users})


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        
        if user:
            token = str(uuid.uuid4())
            user.reset_token = token
            user.reset_token_expiry = timezone.now() + timezone.timedelta(hours=24)
            user.save()
            
            # In a real app, we would send an email here.
            # For now, we'll just show the link in a message for demo purposes.
            reset_url = request.build_absolute_uri(f'/reset-password/{token}/')
            messages.success(request, f'Password reset link generated: {reset_url}')
        else:
            messages.error(request, 'No user found with that email address.')
            
    return render(request, 'accounts/forgot_password.html')


def reset_password(request, token):
    user = User.objects.filter(reset_token=token, reset_token_expiry__gt=timezone.now()).first()
    
    if not user:
        messages.error(request, 'Invalid or expired reset token.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            user.set_password(password)
            user.reset_token = None
            user.reset_token_expiry = None
            user.save()
            messages.success(request, 'Password reset successfully. You can now login.')
            return redirect('login')
            
    return render(request, 'accounts/reset_password.html', {'token': token})


@login_required
def profile_view(request):
    user = request.user
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.bio = request.POST.get('bio', user.bio)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'accounts/profile.html', {'user': user})
