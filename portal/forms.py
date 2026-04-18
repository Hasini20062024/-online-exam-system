from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import Course, Exam, Profile, Question


PASSWORD_HELP = 'Password must have 8+ chars, 1 uppercase, 1 digit, and 1 special character.'


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError('Invalid username or password.')
            cleaned_data['user'] = user
        return cleaned_data


class StudentRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    username = forms.CharField(max_length=150)
    academic_year = forms.CharField(max_length=20)
    password1 = forms.CharField(widget=forms.PasswordInput, help_text=PASSWORD_HELP)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username']
        if not username.isalnum():
            raise forms.ValidationError('Username must be alphanumeric.')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists.')
        return email

    def clean_password1(self):
        password = self.cleaned_data['password1']
        if len(password) < 8:
            raise forms.ValidationError(PASSWORD_HELP)
        if not any(char.isupper() for char in password):
            raise forms.ValidationError(PASSWORD_HELP)
        if not any(char.isdigit() for char in password):
            raise forms.ValidationError(PASSWORD_HELP)
        if all(char.isalnum() for char in password):
            raise forms.ValidationError(PASSWORD_HELP)
        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password1') != cleaned_data.get('password2'):
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
        )
        profile = user.profile
        profile.full_name = self.cleaned_data['full_name']
        profile.role = Profile.ROLE_STUDENT
        profile.academic_year = self.cleaned_data['academic_year']
        profile.save()
        return user


class FacultyCreationForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    username = forms.CharField(max_length=150)
    employee_id = forms.CharField(max_length=20)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if not username.isalnum():
            raise forms.ValidationError('Username must be alphanumeric.')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        return username

    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        if not employee_id.isalnum():
            raise forms.ValidationError('Employee ID must be alphanumeric.')
        if Profile.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError('Employee ID already exists.')
        return employee_id

    def save(self):
        employee_id = self.cleaned_data['employee_id']
        suffix_digits = employee_id[-4:] if len(employee_id) >= 4 else employee_id
        temp_password = f'Temp@{suffix_digits}'
        if len(temp_password) < 8:
            temp_password = temp_password + '1234'

        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=temp_password,
        )
        profile = user.profile
        profile.full_name = self.cleaned_data['full_name']
        profile.role = Profile.ROLE_FACULTY
        profile.employee_id = employee_id
        profile.save()
        return user, temp_password


class CourseForm(forms.ModelForm):
    faculty_members = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(profile__role=Profile.ROLE_FACULTY),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Course
        fields = ['name', 'code', 'description', 'academic_year', 'faculty_members']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty_members'].label_from_instance = (
            lambda user: user.profile.full_name or user.username
        )


class CourseFacultyAssignmentForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all().order_by('code'),
        empty_label='Select course',
    )
    faculty_members = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(profile__role=Profile.ROLE_FACULTY),
        widget=forms.SelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty_members'].label_from_instance = (
            lambda user: user.profile.full_name or user.username
        )


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'course',
            'question_text',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'correct_answer',
            'difficulty',
        ]

    def __init__(self, *args, faculty_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if faculty_user:
            self.fields['course'].queryset = faculty_user.assigned_courses.all()


class ExamForm(forms.ModelForm):
    start_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Exam
        fields = ['title', 'course', 'start_at', 'duration_minutes', 'question_count']

    def __init__(self, *args, faculty_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if faculty_user:
            self.fields['course'].queryset = faculty_user.assigned_courses.all()

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        question_count = cleaned_data.get('question_count')
        if course and question_count and question_count > course.questions.count():
            raise forms.ValidationError('Question count cannot exceed available questions in the bank.')
        return cleaned_data
