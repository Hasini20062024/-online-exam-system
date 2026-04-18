from django.contrib import admin

from .models import AttemptAnswer, Course, Enrollment, Exam, ExamAttempt, ExamRanking, Profile, Question


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'role', 'employee_id', 'academic_year')
    search_fields = ('full_name', 'user__username', 'employee_id')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'academic_year', 'enrolled_count')
    search_fields = ('code', 'name')
    filter_horizontal = ('faculty_members',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('course', 'difficulty', 'correct_answer', 'created_by')
    list_filter = ('course', 'difficulty')


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'faculty', 'start_at', 'duration_minutes', 'question_count')


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'status', 'score', 'percentage', 'submitted_at')
    list_filter = ('status',)
    inlines = [AttemptAnswerInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')


@admin.register(ExamRanking)
class ExamRankingAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'rank', 'score', 'percentage', 'submitted_at')
