import random

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


OPTION_FIELD_MAP = {
    'A': 'option_a',
    'B': 'option_b',
    'C': 'option_c',
    'D': 'option_d',
}


class Profile(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_FACULTY = 'faculty'
    ROLE_STUDENT = 'student'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_FACULTY, 'Faculty'),
        (ROLE_STUDENT, 'Student'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    full_name = models.CharField(max_length=120)
    employee_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        validators=[RegexValidator(r'^[A-Za-z0-9]+$', 'Employee ID must be alphanumeric.')],
    )
    academic_year = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.full_name} ({self.get_role_display()})'


class Course(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    academic_year = models.CharField(max_length=20)
    faculty_members = models.ManyToManyField(
        User,
        blank=True,
        related_name='assigned_courses',
        limit_choices_to={'profile__role': Profile.ROLE_FACULTY},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['academic_year', 'code']

    def __str__(self):
        return f'{self.code} - {self.name}'

    @property
    def enrolled_count(self):
        return self.enrollments.count()


class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'profile__role': Profile.ROLE_STUDENT},
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f'{self.student.username} in {self.course.code}'


class Question(models.Model):
    DIFFICULTY_EASY = 'Easy'
    DIFFICULTY_MEDIUM = 'Medium'
    DIFFICULTY_HARD = 'Hard'

    DIFFICULTY_CHOICES = [
        (DIFFICULTY_EASY, 'Easy'),
        (DIFFICULTY_MEDIUM, 'Medium'),
        (DIFFICULTY_HARD, 'Hard'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions_created')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=[(key, key) for key in OPTION_FIELD_MAP])
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['course__code', '-created_at']

    def __str__(self):
        return f'{self.course.code}: {self.question_text[:50]}'

    @property
    def options(self):
        return {
            'A': self.option_a,
            'B': self.option_b,
            'C': self.option_c,
            'D': self.option_d,
        }

    def get_option_text(self, label):
        return self.options[label]


class Exam(models.Model):
    title = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exams_created')
    start_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(180)]
    )
    question_count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_at']

    def __str__(self):
        return f'{self.title} - {self.course.code}'

    @property
    def end_at(self):
        return self.start_at + timezone.timedelta(minutes=self.duration_minutes)

    @property
    def total_submissions(self):
        return self.attempts.filter(status=ExamAttempt.STATUS_SUBMITTED).count()

    def status(self):
        now = timezone.localtime()
        if now < self.start_at:
            return 'Upcoming'
        if now <= self.end_at:
            return 'Ongoing'
        return 'Completed'


class ExamAttempt(models.Model):
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_SUBMITTED = 'submitted'

    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_SUBMITTED, 'Submitted'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    score = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    time_taken = models.DurationField(blank=True, null=True)

    class Meta:
        unique_together = ('exam', 'student')
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.student.username} - {self.exam.title}'

    @property
    def total_questions(self):
        return self.answers.count()

    @property
    def answered_count(self):
        return self.answers.exclude(selected_option__isnull=True).count()

    @property
    def remaining_seconds(self):
        seconds = int((self.exam.end_at - timezone.localtime()).total_seconds())
        return max(seconds, 0)


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    question_order = models.PositiveIntegerField()
    option_order = models.JSONField(default=list)
    selected_option = models.PositiveSmallIntegerField(blank=True, null=True)
    correct_option = models.PositiveSmallIntegerField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['question_order']
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f'Answer {self.question_order} for {self.attempt}'

    @property
    def shuffled_options(self):
        return [
            {
                'index': index,
                'label': label,
                'text': self.question.get_option_text(label),
            }
            for index, label in enumerate(self.option_order, start=1)
        ]

    @property
    def selected_option_text(self):
        if not self.selected_option:
            return 'Not Attempted'
        label = self.option_order[self.selected_option - 1]
        return self.question.get_option_text(label)

    @property
    def correct_option_text(self):
        label = self.option_order[self.correct_option - 1]
        return self.question.get_option_text(label)


class ExamRanking(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='rankings')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_rankings')
    rank = models.PositiveIntegerField()
    score = models.PositiveIntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    submitted_at = models.DateTimeField()

    class Meta:
        unique_together = ('exam', 'student')
        ordering = ['rank', 'submitted_at']

    def __str__(self):
        return f'{self.exam.title} - {self.student.username} - #{self.rank}'


def build_attempt_answers(attempt):
    questions = list(attempt.exam.course.questions.order_by('?')[: attempt.exam.question_count])
    created_answers = []
    for index, question in enumerate(questions, start=1):
        option_order = list(OPTION_FIELD_MAP.keys())
        random.shuffle(option_order)
        created_answers.append(
            AttemptAnswer(
                attempt=attempt,
                question=question,
                question_order=index,
                option_order=option_order,
                correct_option=option_order.index(question.correct_answer) + 1,
            )
        )
    AttemptAnswer.objects.bulk_create(created_answers)
    return created_answers


def recompute_exam_rankings(exam):
    attempts = list(
        exam.attempts.filter(status=ExamAttempt.STATUS_SUBMITTED)
        .select_related('student')
        .order_by('-score', 'submitted_at', 'id')
    )
    ExamRanking.objects.filter(exam=exam).delete()

    last_score = None
    last_submitted = None
    current_rank = 0
    for index, attempt in enumerate(attempts, start=1):
        if attempt.score == last_score and attempt.submitted_at == last_submitted:
            rank = current_rank
        else:
            rank = index
            current_rank = rank
            last_score = attempt.score
            last_submitted = attempt.submitted_at

        ExamRanking.objects.create(
            exam=exam,
            student=attempt.student,
            rank=rank,
            score=attempt.score,
            percentage=attempt.percentage,
            submitted_at=attempt.submitted_at,
        )
