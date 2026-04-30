from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from django.utils import timezone
from .models import Course, Enrollment, Lesson, Material
from accounts.models import User
from assignments.models import Assignment, Submission, Grade


def course_list(request):
    courses = Course.objects.filter(status='published')
    category = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    
    if category:
        courses = courses.filter(category__iexact=category)
    if difficulty:
        courses = courses.filter(difficulty=difficulty)
    
    categories = Course.objects.filter(status='published').values_list('category', flat=True).distinct()
    
    context = {
        'courses': courses,
        'categories': categories,
        'selected_category': category,
        'selected_difficulty': difficulty,
    }
    return render(request, 'courses/course_list.html', context)


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    is_enrolled = False
    
    if request.user.is_authenticated and request.user.is_student:
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    
    context = {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
        'enrolled_count': course.enrolled_count(),
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def enroll_course(request, course_id):
    if not request.user.is_student:
        messages.error(request, 'Only students can enroll in courses.')
        return redirect('course_detail', course_id=course_id)
    
    course = get_object_or_404(Course, id=course_id)
    
    if course.is_full():
        messages.error(request, 'This course is full.')
        return redirect('course_detail', course_id=course_id)
    
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'status': 'active'}
    )
    
    if created:
        messages.success(request, f'You have successfully enrolled in {course.title}!')
    else:
        messages.info(request, 'You are already enrolled in this course.')
    
    return redirect('course_detail', course_id=course_id)


@login_required
def my_courses(request):
    if not request.user.is_student:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    return render(request, 'courses/my_courses.html', {'enrollments': enrollments})


@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    # Check if user is enrolled or is the instructor
    if request.user != course.instructor and not request.user.is_admin:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        if not enrollment:
            messages.error(request, 'You must be enrolled in this course to view lessons.')
            return redirect('course_detail', course_id=course.id)
    
    materials = lesson.materials.all()
    lessons = course.lessons.all()
    
    context = {
        'lesson': lesson,
        'course': course,
        'materials': materials,
        'lessons': lessons,
    }
    return render(request, 'courses/lesson_detail.html', context)


# Instructor Views
@login_required
def instructor_courses(request):
    if not request.user.is_instructor:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    courses = Course.objects.filter(instructor=request.user)
    return render(request, 'courses/instructor_courses.html', {'courses': courses})


@login_required
def create_course(request):
    if not request.user.is_instructor:
        messages.error(request, 'Only instructors can create courses.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        duration = request.POST.get('duration')
        difficulty = request.POST.get('difficulty', 'beginner')
        max_students = request.POST.get('max_students', 100)
        
        course = Course.objects.create(
            title=title,
            description=description,
            instructor=request.user,
            category=category,
            duration=duration,
            difficulty=difficulty,
            max_students=max_students,
            status='draft'
        )
        
        if 'cover_image' in request.FILES:
            course.cover_image = request.FILES['cover_image']
            course.save()
        
        messages.success(request, 'Course created successfully!')
        return redirect('instructor_courses')
    
    return render(request, 'courses/create_course.html')


@login_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is instructor or admin
    if request.user != course.instructor and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        course.title = request.POST.get('title', course.title)
        course.description = request.POST.get('description', course.description)
        course.category = request.POST.get('category', course.category)
        course.duration = request.POST.get('duration', course.duration)
        course.difficulty = request.POST.get('difficulty', course.difficulty)
        course.max_students = request.POST.get('max_students', course.max_students)
        course.status = request.POST.get('status', course.status)
        
        if 'cover_image' in request.FILES:
            course.cover_image = request.FILES['cover_image']
        
        course.save()
        messages.success(request, 'Course updated successfully!')
        return redirect('instructor_courses') if not request.user.is_admin else redirect('manage_courses')
    
    return render(request, 'courses/edit_course.html', {'course': course})


@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is instructor or admin
    if request.user != course.instructor and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        course_name = course.title
        course.delete()
        messages.success(request, f'Course "{course_name}" deleted successfully.')
        return redirect('instructor_courses') if not request.user.is_admin else redirect('manage_courses')
    
    return render(request, 'courses/delete_confirm.html', {'item': course, 'type': 'course'})


@login_required
def add_lesson(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.user != course.instructor and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        content = request.POST.get('content')
        video_url = request.POST.get('video_url')
        duration = request.POST.get('duration', 30)
        order = request.POST.get('order', 0)
        
        lesson = Lesson.objects.create(
            course=course,
            title=title,
            description=description,
            content=content,
            video_url=video_url,
            duration=duration,
            order=order
        )
        
        messages.success(request, 'Lesson added successfully!')
        return redirect('edit_course', course_id=course.id)
    
    return render(request, 'courses/add_lesson.html', {'course': course})


@login_required
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    if request.user != course.instructor and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        lesson.title = request.POST.get('title', lesson.title)
        lesson.description = request.POST.get('description', lesson.description)
        lesson.content = request.POST.get('content', lesson.content)
        lesson.video_url = request.POST.get('video_url', lesson.video_url)
        lesson.duration = request.POST.get('duration', lesson.duration)
        lesson.order = request.POST.get('order', lesson.order)
        lesson.save()
        
        messages.success(request, 'Lesson updated successfully!')
        return redirect('edit_course', course_id=course.id)
    
    return render(request, 'courses/edit_lesson.html', {'lesson': lesson, 'course': course})


@login_required
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    if request.user != course.instructor and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        lesson_title = lesson.title
        lesson.delete()
        messages.success(request, f'Lesson "{lesson_title}" deleted successfully.')
        return redirect('edit_course', course_id=course.id)
    
    return render(request, 'courses/delete_confirm.html', {'item': lesson, 'type': 'lesson'})


@login_required
def add_material(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    if request.user != course.instructor and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        material_type = request.POST.get('material_type')
        url = request.POST.get('url')
        description = request.POST.get('description')
        
        material = Material.objects.create(
            lesson=lesson,
            title=title,
            material_type=material_type,
            url=url,
            description=description
        )
        
        if 'file' in request.FILES:
            material.file = request.FILES['file']
            material.save()
            
        messages.success(request, 'Material added successfully!')
        return redirect('edit_lesson', lesson_id=lesson.id)
        
    return render(request, 'courses/add_material.html', {'lesson': lesson})


@login_required
def delete_material(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    lesson = material.lesson
    
    if request.user != lesson.course.instructor and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        material_title = material.title
        material.delete()
        messages.success(request, f'Material "{material_title}" deleted successfully.')
        return redirect('edit_lesson', lesson_id=lesson.id)
        
    return render(request, 'courses/delete_confirm.html', {'item': material, 'type': 'material'})


# Admin Views
@login_required
def manage_courses(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    courses = Course.objects.all().select_related('instructor')
    return render(request, 'courses/manage_courses.html', {'courses': courses})


@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    context = {
        'total_users': User.objects.count(),
        'total_courses': Course.objects.count(),
        'total_enrollments': Enrollment.objects.count(),
        'recent_users': User.objects.order_by('-created_at')[:10],
        'recent_courses': Course.objects.order_by('-created_at')[:10],
    }
    return render(request, 'courses/admin_dashboard.html', context)
