from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Avg, Count
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
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.GET.get('next', 'dashboard')
        
        # Try to authenticate with username first
        user = authenticate(request, username=username_or_email, password=password)
        
        # If username fails, try to find user by email and authenticate
        if user is None:
            try:
                temp_user = User.objects.get(email=username_or_email)
                user = authenticate(request, username=temp_user.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(next_url if next_url else 'dashboard')
        else:
            messages.error(request, 'Invalid username/email or password.')
    
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
    
    if user.is_admin:
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
        
        # Real Activity for Admin
        recent_users = User.objects.exclude(id=user.id).order_by('-created_at')[:5]
        context['recent_activity'] = [
            {'title': 'New User', 'description': f'{u.get_full_name() or u.username} joined the platform as {u.role}.'}
            for u in recent_users
        ]
        
    elif user.is_instructor:
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
        
        # Top Students for this Instructor
        top_students = User.objects.filter(
            submissions__assignment__course__instructor=user,
            submissions__grade__isnull=False
        ).annotate(
            avg_score=Avg('submissions__grade__score')
        ).order_by('-avg_score')[:5]
        
        context['top_students'] = [
            {
                'name': s.get_full_name() or s.username,
                'avg_score': round(s.avg_score, 1) if s.avg_score else 0,
                'initials': (s.first_name[0] if s.first_name else s.username[0]).upper()
            } for s in top_students
        ]
        
        # Real Activity for Instructor
        activity = []
        recent_submissions = Submission.objects.filter(assignment__course__instructor=user).order_by('-submitted_at')[:3]
        for sub in recent_submissions:
            activity.append({
                'title': 'New Submission',
                'description': f'{sub.student.get_full_name() or sub.student.username} submitted "{sub.assignment.title}".'
            })
            
        recent_enrollments = Enrollment.objects.filter(course__instructor=user).order_by('-enrolled_at')[:3]
        for enr in recent_enrollments:
            activity.append({
                'title': 'Course Enrollment',
                'description': f'{enr.student.get_full_name() or enr.student.username} enrolled in "{enr.course.title}".'
            })
            
        context['recent_activity'] = sorted(activity, key=lambda x: x['title'], reverse=True)[:5]
        
    else:  # Student
        enrollments = Enrollment.objects.filter(student=user).select_related('course', 'course__instructor').order_by('-enrolled_at')
        context['enrolled_courses_count'] = enrollments.count()
        
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
            grade_list = []
            for g in grades:
                if g.submission.assignment.max_score > 0:
                    grade_list.append(float(g.score) / float(g.submission.assignment.max_score) * 100)
            if grade_list:
                context['average_grade'] = round(sum(grade_list) / len(grade_list), 1)
        
        # Real Activity for Student
        activity = []
        recent_grades = Grade.objects.filter(submission__student=user).order_by('-graded_at')[:3]
        for grade in recent_grades:
            activity.append({
                'title': 'Assignment Graded',
                'description': f'Your submission for "{grade.submission.assignment.title}" was graded: {grade.score}/{grade.submission.assignment.max_score}.'
            })
            
        upcoming_assignments = Assignment.objects.filter(course__enrollments__student=user, due_date__gt=timezone.now()).order_by('due_date')[:3]
        for ass in upcoming_assignments:
            activity.append({
                'title': 'Upcoming Deadline',
                'description': f'"{ass.title}" for {ass.course.title} is due on {ass.due_date.strftime("%b %d, %H:%M")}.'
            })
            
        context['recent_activity'] = activity[:5]
    
    return render(request, 'dashboard.html', context)


@login_required
def manage_users(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    users = User.objects.all().order_by('-created_at')
    return render(request, 'accounts/manage_users.html', {'users': users})


@login_required
def delete_user(request, user_id):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    target_user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deletion
    if request.user.id == target_user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('manage_users')
        
    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f'User "{username}" deleted successfully.')
        return redirect('manage_users')
        
    return render(request, 'accounts/delete_confirm.html', {'item': target_user, 'type': 'user'})


@login_required
def edit_user_admin(request, user_id):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
        
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        target_user.username = request.POST.get('username', target_user.username)
        target_user.email = request.POST.get('email', target_user.email)
        target_user.first_name = request.POST.get('first_name', target_user.first_name)
        target_user.last_name = request.POST.get('last_name', target_user.last_name)
        target_user.role = request.POST.get('role', target_user.role)
        target_user.is_active = 'is_active' in request.POST
        target_user.save()
        
        messages.success(request, f'User "{target_user.username}" updated successfully.')
        return redirect('manage_users')
        
    return render(request, 'accounts/edit_user_admin.html', {'target_user': target_user})


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
