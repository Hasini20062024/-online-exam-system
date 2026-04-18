from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('courses/<int:course_id>/enroll/', views.enroll_in_course, name='enroll_course'),
    path('faculty/create/', views.create_faculty, name='create_faculty'),
    path('courses/create/', views.create_course, name='create_course'),
    path('courses/<int:course_id>/assign-faculty/', views.assign_faculty_to_course, name='assign_faculty_to_course'),
    path('questions/create/', views.create_question, name='create_question'),
    path('questions/upload-excel/', views.upload_questions_excel, name='upload_questions_excel'),
    path('exams/create/', views.create_exam, name='create_exam'),
    path('exams/<int:exam_id>/start/', views.start_exam, name='start_exam'),
    path('attempts/<int:attempt_id>/submit/', views.submit_exam, name='submit_exam'),
    path('results/<int:attempt_id>/', views.result_detail, name='result_detail'),
    path('faculty/exams/<int:exam_id>/results/', views.faculty_exam_results, name='faculty_exam_results'),
    path('faculty/exams/<int:exam_id>/results/export/', views.export_exam_results_csv, name='export_exam_results_csv'),
]
