import io

from openpyxl import Workbook
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Course, Enrollment, Exam, ExamAttempt, ExamRanking, Profile, Question, build_attempt_answers


class PortalFlowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='student1', password='Test@123', email='s1@test.com')
        self.student.profile.full_name = 'Student One'
        self.student.profile.academic_year = '2025-26'
        self.student.profile.save()

        self.faculty = User.objects.create_user(username='faculty1', password='Test@123', email='f1@test.com')
        self.faculty.profile.full_name = 'Faculty One'
        self.faculty.profile.role = Profile.ROLE_FACULTY
        self.faculty.profile.employee_id = 'EMP1001'
        self.faculty.profile.save()

        self.course = Course.objects.create(
            name='Database Systems',
            code='CS301',
            description='Core DBMS course',
            academic_year='2025-26',
        )
        self.course.faculty_members.add(self.faculty)
        Enrollment.objects.create(course=self.course, student=self.student)

        for index in range(4):
            Question.objects.create(
                course=self.course,
                created_by=self.faculty,
                question_text=f'Question {index + 1}',
                option_a='A1',
                option_b='B1',
                option_c='C1',
                option_d='D1',
                correct_answer='A',
                difficulty=Question.DIFFICULTY_EASY,
            )

        self.exam = Exam.objects.create(
            title='Mid Exam',
            course=self.course,
            faculty=self.faculty,
            start_at=timezone.localtime() - timezone.timedelta(minutes=5),
            duration_minutes=30,
            question_count=3,
        )

    def test_register_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_start_exam_creates_attempt(self):
        self.client.login(username='student1', password='Test@123')
        response = self.client.get(reverse('start_exam', args=[self.exam.id]))
        self.assertEqual(response.status_code, 200)
        attempt = ExamAttempt.objects.get(exam=self.exam, student=self.student)
        self.assertEqual(attempt.answers.count(), 3)

    def test_submit_exam_generates_ranking(self):
        attempt = ExamAttempt.objects.create(exam=self.exam, student=self.student)
        build_attempt_answers(attempt)
        payload = {f'question_{answer.id}': answer.correct_option for answer in attempt.answers.all()}

        self.client.login(username='student1', password='Test@123')
        response = self.client.post(reverse('submit_exam', args=[attempt.id]), payload)
        self.assertEqual(response.status_code, 302)

        attempt.refresh_from_db()
        ranking = ExamRanking.objects.get(exam=self.exam, student=self.student)
        self.assertEqual(attempt.score, 3)
        self.assertEqual(ranking.rank, 1)

    def test_faculty_excel_upload_creates_questions(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'difficulty'])
        sheet.append(['What is SQL?', 'Lang', 'OS', 'CPU', 'IDE', 'A', 'Easy'])
        file_stream = io.BytesIO()
        workbook.save(file_stream)
        file_stream.seek(0)

        uploaded_file = SimpleUploadedFile(
            'questions.xlsx',
            file_stream.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        self.client.login(username='faculty1', password='Test@123')
        response = self.client.post(
            reverse('upload_questions_excel'),
            {
                'academic_year': self.course.academic_year,
                'course_id': self.course.id,
                'question_file': uploaded_file,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Question.objects.filter(course=self.course, question_text='What is SQL?').exists())
