from django.db import models
from accounts.models import User
from courses.models import Course, Lesson


class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('quiz', 'Quiz'),
        ('essay', 'Essay'),
        ('project', 'Project'),
        ('homework', 'Homework'),
        ('exam', 'Exam'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assignments', blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='homework')
    max_score = models.PositiveIntegerField(default=100)
    due_date = models.DateTimeField()
    instructions = models.TextField(blank=True, null=True)
    allow_late_submission = models.BooleanField(default=False)
    late_penalty_percent = models.PositiveIntegerField(default=0, help_text="Penalty percentage for late submission")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-due_date']
    
    def __str__(self):
        return f"{self.title} - {self.course.title}"


class Submission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('late', 'Late'),
        ('resubmit', 'Resubmit Required'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions', limit_choices_to={'role': 'student'})
    content = models.TextField(blank=True, null=True, help_text="Text submission content")
    file = models.FileField(upload_to='assignments/submissions/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    is_late = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['assignment', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"


class Grade(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='grade')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    feedback = models.TextField(blank=True, null=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='grades_given', limit_choices_to={'role': 'instructor'})
    graded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.submission.student.username} - {self.score}/{self.submission.assignment.max_score}"
    
    def percentage(self):
        if self.submission.assignment.max_score > 0:
            return (self.score / self.submission.assignment.max_score) * 100
        return 0
    
    def letter_grade(self):
        percentage = self.percentage()
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'


class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.option_text


class StudentAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    selected_option = models.ForeignKey(AnswerOption, on_delete=models.CASCADE, blank=True, null=True)
    text_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['question', 'submission']
    
    def __str__(self):
        return f"{self.submission.student.username} - {self.question.question_text[:30]}..."
