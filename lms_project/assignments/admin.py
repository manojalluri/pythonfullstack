from django.contrib import admin
from .models import Assignment, Submission, Grade, Question, AnswerOption, StudentAnswer


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'assignment_type', 'max_score', 'due_date', 'created_at']
    list_filter = ['assignment_type', 'course', 'created_at']
    search_fields = ['title', 'course__title']
    inlines = [QuestionInline]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'status', 'submitted_at', 'is_late']
    list_filter = ['status', 'is_late', 'submitted_at']
    search_fields = ['student__username', 'assignment__title']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['submission', 'score', 'letter_grade', 'graded_by', 'graded_at']
    list_filter = ['graded_at']
    search_fields = ['submission__student__username', 'submission__assignment__title']
    
    def letter_grade(self, obj):
        return obj.letter_grade()
    letter_grade.short_description = 'Grade'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'assignment', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'assignment']
    inlines = [AnswerOptionInline]


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ['option_text', 'question', 'is_correct']
    list_filter = ['is_correct']


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'submission', 'is_correct', 'points_earned']
    list_filter = ['is_correct']
