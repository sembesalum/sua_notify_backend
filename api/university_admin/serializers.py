from rest_framework import serializers
from .models import University, Course, Semester, User, Timetable, Notification, Task
from django.contrib.auth.hashers import make_password

class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email', 
                  'phone_number', 'user_type', 'registration_number', 
                  'assigned_course', 'assigned_semester']
    
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class TimetableSerializer(serializers.ModelSerializer):
    lecturer_name = serializers.CharField(source='lecturer.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True)
    
    class Meta:
        model = Timetable
        fields = [
            'id', 'subject_code', 'subject_name', 'lecturer', 'lecturer_name',
            'venue', 'start_time', 'end_time', 'day', 'color_code', 'status',
            'cancellation_note', 'course', 'course_name', 'semester', 'semester_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'created_by', 'cancellation_note', 'created_at', 'updated_at']

class TimetableUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timetable
        fields = ['status', 'cancellation_note']
        
# Add this to your serializers.py
class TimetableStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['CONFIRMED', 'CANCELLED'])
    cancellation_note = serializers.CharField(required=False, allow_blank=True)
    lecturer_id = serializers.IntegerField(required=True)

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['is_read', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_at']