from django.contrib import admin
from .models import Course, Enrollment, Lesson, Material


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'category', 'difficulty', 'status', 'enrolled_count', 'created_at']
    list_filter = ['status', 'difficulty', 'category', 'created_at']
    search_fields = ['title', 'description', 'instructor__username']
    inlines = [LessonInline]
    
    def enrolled_count(self, obj):
        return obj.enrolled_count()


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'progress', 'enrolled_at']
    list_filter = ['status', 'enrolled_at']
    search_fields = ['student__username', 'course__title']


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 1


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'duration', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['title', 'course__title']
    inlines = [MaterialInline]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'material_type', 'uploaded_at']
    list_filter = ['material_type', 'uploaded_at']
    search_fields = ['title', 'lesson__title']
