from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Assignment, Submission, Grade, Question, AnswerOption, StudentAnswer
from courses.models import Course, Enrollment


@login_required
def my_assignments(request):
    if not request.user.is_student:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get enrolled courses
    enrollments = Enrollment.objects.filter(student=request.user)
    course_ids = enrollments.values_list('course_id', flat=True)
    
    # Get assignments for enrolled courses
    assignments = Assignment.objects.filter(course_id__in=course_ids).select_related('course')
    
    # Get submissions and attach to assignments
    submissions = {s.assignment_id: s for s in Submission.objects.filter(student=request.user)}
    for assignment in assignments:
        assignment.user_submission = submissions.get(assignment.id)
    
    context = {
        'assignments': assignments,
    }
    return render(request, 'assignments/my_assignments.html', context)


@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if not request.user.is_student:
        messages.error(request, 'Only students can submit assignments.')
        return redirect('dashboard')
    
    # Check if enrolled
    if not Enrollment.objects.filter(student=request.user, course=assignment.course).exists():
        messages.error(request, 'You must be enrolled in this course to submit assignments.')
        return redirect('course_detail', course_id=assignment.course.id)
    
    # Check if already submitted
    submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    
    if request.method == 'POST':
        content = request.POST.get('content', '')
        
        is_late = timezone.now() > assignment.due_date
        
        if submission:
            submission.content = content
            submission.is_late = is_late
            submission.status = 'submitted'
            if 'file' in request.FILES:
                submission.file = request.FILES['file']
            submission.save()
        else:
            submission = Submission.objects.create(
                assignment=assignment,
                student=request.user,
                content=content,
                is_late=is_late,
                status='submitted'
            )
            if 'file' in request.FILES:
                submission.file = request.FILES['file']
                submission.save()
        
        messages.success(request, 'Assignment submitted successfully!')
        return redirect('my_assignments')
    
    context = {
        'assignment': assignment,
        'submission': submission,
    }
    return render(request, 'assignments/submit_assignment.html', context)


@login_required
def my_grades(request):
    if not request.user.is_student:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    grades = Grade.objects.filter(submission__student=request.user).select_related('submission__assignment')
    return render(request, 'assignments/my_grades.html', {'grades': grades})


# Instructor Views
@login_required
def instructor_assignments(request):
    if not request.user.is_instructor:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    assignments = Assignment.objects.filter(course__instructor=request.user).select_related('course')
    return render(request, 'assignments/instructor_assignments.html', {'assignments': assignments})


@login_required
def create_assignment(request):
    if not request.user.is_instructor and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    courses = Course.objects.filter(instructor=request.user) if not request.user.is_admin else Course.objects.all()
    
    if request.method == 'POST':
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        description = request.POST.get('description')
        assignment_type = request.POST.get('assignment_type', 'homework')
        max_score = request.POST.get('max_score', 100)
        due_date = request.POST.get('due_date')
        instructions = request.POST.get('instructions')
        
        assignment = Assignment.objects.create(
            course_id=course_id,
            title=title,
            description=description,
            assignment_type=assignment_type,
            max_score=max_score,
            due_date=due_date,
            instructions=instructions
        )
        
        messages.success(request, 'Assignment created successfully!')
        return redirect('instructor_assignments')
    
    return render(request, 'assignments/create_assignment.html', {'courses': courses})


@login_required
def edit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if request.user != assignment.course.instructor and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    courses = Course.objects.filter(instructor=request.user) if not request.user.is_admin else Course.objects.all()
    
    if request.method == 'POST':
        assignment.course_id = request.POST.get('course', assignment.course_id)
        assignment.title = request.POST.get('title', assignment.title)
        assignment.description = request.POST.get('description', assignment.description)
        assignment.assignment_type = request.POST.get('assignment_type', assignment.assignment_type)
        assignment.max_score = request.POST.get('max_score', assignment.max_score)
        assignment.due_date = request.POST.get('due_date', assignment.due_date)
        assignment.instructions = request.POST.get('instructions', assignment.instructions)
        assignment.save()
        
        messages.success(request, 'Assignment updated successfully!')
        return redirect('instructor_assignments')
    
    return render(request, 'assignments/edit_assignment.html', {'assignment': assignment, 'courses': courses})


@login_required
def delete_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if request.user != assignment.course.instructor and not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = assignment.title
        assignment.delete()
        messages.success(request, f'Assignment "{title}" deleted successfully.')
        return redirect('instructor_assignments')
    
    return render(request, 'assignments/delete_confirm.html', {'item': assignment, 'type': 'assignment'})


@login_required
def submissions_pending(request):
    if not request.user.is_instructor:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    submissions = Submission.objects.filter(
        assignment__course__instructor=request.user,
        status='submitted'
    ).select_related('assignment', 'student')
    
    return render(request, 'assignments/submissions_pending.html', {'submissions': submissions})


@login_required
def grade_submission(request, submission_id):
    if not request.user.is_instructor:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    submission = get_object_or_404(Submission, id=submission_id, assignment__course__instructor=request.user)
    
    if request.method == 'POST':
        score = request.POST.get('score')
        feedback = request.POST.get('feedback', '')
        
        grade, created = Grade.objects.get_or_create(
            submission=submission,
            defaults={
                'score': score,
                'feedback': feedback,
                'graded_by': request.user
            }
        )
        
        if not created:
            grade.score = score
            grade.feedback = feedback
            grade.graded_by = request.user
            grade.save()
        
        submission.status = 'graded'
        submission.save()
        
        messages.success(request, 'Submission graded successfully!')
        return redirect('submissions_pending')
    
    return render(request, 'assignments/grade_submission.html', {'submission': submission})


@login_required
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check permissions
    if request.user != assignment.course.instructor and not request.user.is_admin:
        enrollment = Enrollment.objects.filter(student=request.user, course=assignment.course).first()
        if not enrollment:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    
    submissions = None
    if request.user == assignment.course.instructor or request.user.is_admin:
        submissions = Submission.objects.filter(assignment=assignment).select_related('student')
    else:
        submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
        submissions = [submission] if submission else []
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
    }
    return render(request, 'assignments/assignment_detail.html', context)
