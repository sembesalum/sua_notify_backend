from django import forms
from .models import University, Course, Semester, User

class UniversityForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['name']

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['university', 'name', 'code']

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['university', 'course', 'name', 'start_date', 'end_date']

class LectureForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'phone_number']

class MonitorForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'registration_number', 'phone_number', 'assigned_course', 'assigned_semester']