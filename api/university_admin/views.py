from datetime import datetime
import logging
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login
from rest_framework import viewsets, status
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.auth.hashers import check_password
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
from datetime import datetime, time
import re
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import (
    University, Course, Semester, User,
    Timetable, Notification, Task
)
from .serializers import (
    TimetableStatusSerializer, UniversitySerializer, CourseSerializer, SemesterSerializer,
    UserSerializer, TimetableSerializer, NotificationSerializer,
    TaskSerializer
)
from .forms import (
    UniversityForm, CourseForm, SemesterForm,
    LectureForm, MonitorForm
)
from university_admin import serializers

logger = logging.getLogger(__name__)

# ==============================================
# ADMIN VIEWS
# ==============================================

class AdminDashboard(View):
    template_name = 'timetable/admin_dashboard.html'
    
    def get(self, request):
        universities = University.objects.all().order_by('-created_at')
        courses = Course.objects.all().order_by('-created_at')
        lectures = User.objects.filter(user_type='LECTURE').order_by('-date_joined')
        monitors = User.objects.filter(user_type='MONITOR').order_by('-date_joined')
        semesters = Semester.objects.all().order_by('-created_at')
        
        context = {
            'universities': universities,
            'courses': courses,
            'lectures': lectures,
            'monitors': monitors,
            'semesters': semesters,
        }
        return render(request, self.template_name, context)

# University CRUD Views
class UniversityCreateView(View):
    template_name = 'timetable/university_form.html'
    
    def get(self, request):
        form = UniversityForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = UniversityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form})

class UniversityUpdateView(View):
    template_name = 'timetable/university_form.html'
    
    def get(self, request, pk):
        university = get_object_or_404(University, pk=pk)
        form = UniversityForm(instance=university)
        return render(request, self.template_name, {'form': form, 'university': university})
    
    def post(self, request, pk):
        university = get_object_or_404(University, pk=pk)
        form = UniversityForm(request.POST, instance=university)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form, 'university': university})

class UniversityDeleteView(View):
    def post(self, request, pk):
        university = get_object_or_404(University, pk=pk)
        university.delete()
        messages.success(request, 'University deleted successfully!')
        return redirect('admin_dashboard')

# Course CRUD Views
class CourseCreateView(View):
    template_name = 'timetable/course_form.html'
    
    def get(self, request):
        form = CourseForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form})

class CourseUpdateView(View):
    template_name = 'timetable/course_form.html'
    
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        form = CourseForm(instance=course)
        return render(request, self.template_name, {'form': form, 'course': course})
    
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form, 'course': course})

class CourseDeleteView(View):
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('admin_dashboard')

# Semester CRUD Views
class SemesterCreateView(View):
    template_name = 'timetable/semester_form.html'
    
    def get(self, request):
        form = SemesterForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = SemesterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form})

class SemesterUpdateView(View):
    template_name = 'timetable/semester_form.html'
    
    def get(self, request, pk):
        semester = get_object_or_404(Semester, pk=pk)
        form = SemesterForm(instance=semester)
        return render(request, self.template_name, {'form': form, 'semester': semester})
    
    def post(self, request, pk):
        semester = get_object_or_404(Semester, pk=pk)
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form, 'semester': semester})

class SemesterDeleteView(View):
    def post(self, request, pk):
        semester = get_object_or_404(Semester, pk=pk)
        semester.delete()
        messages.success(request, 'Semester deleted successfully!')
        return redirect('admin_dashboard')

# Lecture CRUD Views
class LectureCreateView(View):
    template_name = 'timetable/lecture_form.html'
    
    def get(self, request):
        form = LectureForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = LectureForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'LECTURE'
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form})

class LectureUpdateView(View):
    template_name = 'timetable/lecture_form.html'
    
    def get(self, request, pk):
        lecture = get_object_or_404(User, pk=pk, user_type='LECTURE')
        form = LectureForm(instance=lecture)
        return render(request, self.template_name, {'form': form, 'lecture': lecture})
    
    def post(self, request, pk):
        lecture = get_object_or_404(User, pk=pk, user_type='LECTURE')
        form = LectureForm(request.POST, instance=lecture)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form, 'lecture': lecture})

class LectureDeleteView(View):
    def post(self, request, pk):
        lecture = get_object_or_404(User, pk=pk, user_type='LECTURE')
        lecture.delete()
        messages.success(request, 'Lecture deleted successfully!')
        return redirect('admin_dashboard')

# Monitor CRUD Views
class MonitorCreateView(View):
    template_name = 'timetable/monitor_form.html'
    
    def get(self, request):
        form = MonitorForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = MonitorForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'MONITOR'
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form})

class MonitorUpdateView(View):
    template_name = 'timetable/monitor_form.html'
    
    def get(self, request, pk):
        monitor = get_object_or_404(User, pk=pk, user_type='MONITOR')
        form = MonitorForm(instance=monitor)
        return render(request, self.template_name, {'form': form, 'monitor': monitor})
    
    def post(self, request, pk):
        monitor = get_object_or_404(User, pk=pk, user_type='MONITOR')
        form = MonitorForm(request.POST, instance=monitor)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form, 'monitor': monitor})

class MonitorDeleteView(View):
    def post(self, request, pk):
        monitor = get_object_or_404(User, pk=pk, user_type='MONITOR')
        monitor.delete()
        messages.success(request, 'Monitor deleted successfully!')
        return redirect('admin_dashboard')

# ==============================================
# AUTHENTICATION VIEWS
# ==============================================

class MonitorLoginView(APIView):
    def post(self, request):
        reg_number = request.data.get('registration_number')
        password = request.data.get('password')
        
        if not reg_number or not password:
            return Response(
                {'error': 'Both registration number and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(registration_number=reg_number, user_type='MONITOR')
            
            if check_password(password, user.password):
                return Response({
                    'status': 'success',
                    'user_id': user.id,
                    'username': user.username,
                    'registration_number': user.registration_number,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                })
            return Response(
                {'error': 'Invalid password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        except User.DoesNotExist:
            return Response(
                {'error': 'No monitor account found with this registration number'},
                status=status.HTTP_404_NOT_FOUND
            )

class LectureLoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Both email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email, user_type='LECTURE')
            
            if check_password(password, user.password):
                return Response({
                    'status': 'success',
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                })
            return Response(
                {'error': 'Invalid password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        except User.DoesNotExist:
            return Response(
                {'error': 'No lecture account found with this email'},
                status=status.HTTP_404_NOT_FOUND
            )

# ==============================================
# API VIEWS (ViewSets)
# ==============================================

class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    
    def get_queryset(self):
        user_id = self.request.data.get('user_id')
        if not user_id:
            raise PermissionDenied('User ID required')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise PermissionDenied('User not found')
        
        queryset = super().get_queryset()
        
        if user.user_type == 'LECTURE':
            return queryset.filter(lecturer=user)
        elif user.user_type == 'MONITOR':
            return queryset.filter(created_by=user)
        else:
            return queryset.none()
    
    def create(self, request, *args, **kwargs):
        monitor_id = request.data.get('monitor_id')
        lecturer_id = request.data.get('lecturer_id')
        
        if not monitor_id or not lecturer_id:
            return Response(
                {'error': 'Both monitor_id and lecturer_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            monitor = User.objects.get(id=monitor_id, user_type='MONITOR')
            lecturer = User.objects.get(id=lecturer_id, user_type='LECTURE')
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid monitor or lecture ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        timetable_data = {
            'subject_code': request.data.get('subject_code'),
            'subject_name': request.data.get('subject_name'),
            'lecturer': lecturer.id,
            'venue': request.data.get('venue'),
            'start_time': request.data.get('start_time'),
            'end_time': request.data.get('end_time'),
            'day': request.data.get('day'),
            'color_code': request.data.get('color_code', '#FFFFFF'),
            'course': request.data.get('course_id'),
            'semester': request.data.get('semester_id'),
            'created_by': monitor.id,
            'status': 'PENDING'
        }
        
        serializer = self.get_serializer(data=timetable_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        lecture_id = request.data.get('lecture_id')
        if not lecture_id:
            return Response(
                {'error': 'lecture_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lecture = User.objects.get(id=lecture_id, user_type='LECTURE')
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid lecture ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        timetable = self.get_object()
        
        if timetable.lecturer != lecture:
            return Response(
                {'error': 'You can only update your own timetables'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TimetableStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        timetable.status = serializer.validated_data['status']
        if timetable.status == 'CANCELLED':
            timetable.cancellation_note = serializer.validated_data.get('cancellation_note', '')
        
        timetable.save()
        
        Notification.objects.create(
            user=timetable.created_by,
            message=f"Your timetable for {timetable.subject_name} has been {timetable.status.lower()}",
            timetable=timetable
        )
        
        return Response({'status': 'success'})

class TimetableCreateView(APIView):
    def _parse_time(self, time_str):
        if isinstance(time_str, time):
            return time_str
            
        time_str = str(time_str).strip()
        
        for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M%p'):
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
                
        if re.match(r'^\d{1,2}:\d{2}$', time_str):
            try:
                return datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                pass
                
        if re.match(r'^\d{1,2}:\d{2}\s*[ap]m$', time_str.lower()):
            try:
                return datetime.strptime(time_str, '%I:%M %p').time()
            except ValueError:
                pass
                
        raise ValueError(f"Invalid time format: {time_str}. Accepted formats: HH:MM:SS, HH:MM, H:MM AM/PM")

    def post(self, request):
        errors = {}
        
        required_fields = {
            'monitor_id': 'Monitor ID is required',
            'lecturer_id': 'Lecturer ID is required',
            'course_id': 'Course ID is required',
            'semester_id': 'Semester ID is required',
            'subject_code': 'Subject code is required',
            'subject_name': 'Subject name is required',
            'venue': 'Venue is required',
            'start_time': 'Start time is required',
            'end_time': 'End time is required',
            'day': 'Day is required'
        }

        for field, message in required_fields.items():
            if field not in request.data or not request.data[field]:
                errors[field] = message

        start_time = end_time = None
        if 'start_time' in request.data and 'end_time' in request.data:
            try:
                start_time = self._parse_time(request.data['start_time'])
                end_time = self._parse_time(request.data['end_time'])
                
                if end_time <= start_time:
                    errors['time'] = 'End time must be after start time'
            except ValueError as e:
                errors['time'] = str(e)

        if 'day' in request.data:
            day = request.data['day'].upper()
            if day not in dict(Timetable.DAY_CHOICES):
                errors['day'] = f'Invalid day. Must be one of: {", ".join(dict(Timetable.DAY_CHOICES).keys())}'

        if errors:
            return Response(
                {'error': 'Validation failed', 'details': errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            monitor = User.objects.get(id=request.data['monitor_id'], user_type='MONITOR')
            lecturer = User.objects.get(id=request.data['lecturer_id'], user_type='LECTURE')
            course = Course.objects.get(id=request.data['course_id'])
            semester = Semester.objects.get(id=request.data['semester_id'], course=course)

            timetable = Timetable(
                subject_code=request.data['subject_code'],
                subject_name=request.data['subject_name'],
                lecturer=lecturer,
                venue=request.data['venue'],
                start_time=start_time,
                end_time=end_time,
                day=day,
                color_code=request.data.get('color_code', '#FFFFFF'),
                course=course,
                semester=semester,
                created_by=monitor,
                status='PENDING'
            )
            timetable.save()

            serializer = TimetableSerializer(timetable)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except User.DoesNotExist as e:
            return Response(
                {'error': 'User validation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (Course.DoesNotExist, Semester.DoesNotExist) as e:
            return Response(
                {'error': 'Course/Semester validation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Creation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
class TimetableUpdateView(APIView):
    def _parse_time(self, time_str):
        # Reuse the same time parsing method from create view
        if isinstance(time_str, time):
            return time_str
            
        time_str = str(time_str).strip()
        
        for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M%p'):
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
                
        if re.match(r'^\d{1,2}:\d{2}$', time_str):
            try:
                return datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                pass
                
        if re.match(r'^\d{1,2}:\d{2}\s*[ap]m$', time_str.lower()):
            try:
                return datetime.strptime(time_str, '%I:%M %p').time()
            except ValueError:
                pass
                
        raise ValueError(f"Invalid time format: {time_str}")

    def put(self, request, pk):
        try:
            timetable = Timetable.objects.get(pk=pk)
        except Timetable.DoesNotExist:
            return Response(
                {'error': 'Timetable not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        errors = {}
        data = request.data

        # Validate required fields
        if 'start_time' in data and 'end_time' in data:
            try:
                start_time = self._parse_time(data['start_time'])
                end_time = self._parse_time(data['end_time'])
                
                if end_time <= start_time:
                    errors['time'] = 'End time must be after start time'
                else:
                    timetable.start_time = start_time
                    timetable.end_time = end_time
            except ValueError as e:
                errors['time'] = str(e)

        if 'day' in data:
            day = data['day'].upper()
            if day in dict(Timetable.DAY_CHOICES):
                timetable.day = day
            else:
                errors['day'] = f'Invalid day. Must be one of: {", ".join(dict(Timetable.DAY_CHOICES).keys())}'

        if errors:
            return Response(
                {'error': 'Validation failed', 'details': errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update other fields
        if 'subject_code' in data:
            timetable.subject_code = data['subject_code']
        if 'subject_name' in data:
            timetable.subject_name = data['subject_name']
        if 'venue' in data:
            timetable.venue = data['venue']
        if 'color_code' in data:
            timetable.color_code = data['color_code']
        if 'status' in data and data['status'] in dict(Timetable.STATUS_CHOICES):
            timetable.status = data['status']

        try:
            if 'lecturer_id' in data:
                lecturer = User.objects.get(id=data['lecturer_id'], user_type='LECTURE')
                timetable.lecturer = lecturer
            if 'course_id' in data:
                course = Course.objects.get(id=data['course_id'])
                timetable.course = course
            if 'semester_id' in data:
                semester = Semester.objects.get(id=data['semester_id'], course=timetable.course)
                timetable.semester = semester
        except (User.DoesNotExist, Course.DoesNotExist, Semester.DoesNotExist) as e:
            return Response(
                {'error': 'Validation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        timetable.save()
        serializer = TimetableSerializer(timetable)
        return Response(serializer.data)

class TimetableDeleteView(APIView):
    def delete(self, request, pk):
        try:
            timetable = Timetable.objects.get(pk=pk)
            timetable.delete()
            return Response(
                {'status': 'success', 'message': 'Timetable deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Timetable.DoesNotExist:
            return Response(
                {'error': 'Timetable not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class TimetableView(ListAPIView):
    serializer_class = TimetableSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'day', 'course', 'semester']
    
    def get_queryset(self):
        queryset = Timetable.objects.all().select_related(
            'lecturer', 'created_by', 'course', 'semester'
        ).order_by('day', 'start_time')
        
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status.upper())
        
        return queryset
    
class MonitorTimetableByIdView(APIView):
    def get(self, request, monitor_id):
        try:
            User.objects.get(id=monitor_id, user_type='MONITOR')
            
            timetables = Timetable.objects.filter(
                created_by_id=monitor_id
            ).select_related(
                'lecturer', 'course', 'semester'
            ).order_by('-created_at')
            
            serializer = TimetableSerializer(timetables, many=True)
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Monitor with this ID does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
            
class LectureTimetableByIdView(APIView):
    def get(self, request, lecture_id):
        try:
            User.objects.get(id=lecture_id, user_type='LECTURE')
            
            timetables = Timetable.objects.filter(
                lecturer_id=lecture_id
            ).select_related(
                'created_by', 'course', 'semester'
            ).order_by('day', 'start_time')
            
            serializer = TimetableSerializer(timetables, many=True)
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Lecturer with this ID does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
    
class TimetableStatusUpdateView(APIView):
    def patch(self, request, timetable_id):
        try:
            timetable = Timetable.objects.get(id=timetable_id)
        except Timetable.DoesNotExist:
            return Response(
                {'error': 'Timetable not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        lecturer_id = request.data.get('lecturer_id')
        if not lecturer_id:
            return Response(
                {'error': 'lecturer_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lecturer = User.objects.get(id=lecturer_id, user_type='LECTURE')
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid lecturer ID'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if timetable.lecturer != lecturer:
            return Response(
                {'error': 'You can only update your own timetables'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TimetableStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        timetable.status = serializer.validated_data['status']
        if timetable.status == 'CANCELLED':
            timetable.cancellation_note = serializer.validated_data.get('cancellation_note', '')
        
        timetable.save()

        # Create notification
        notification = Notification.objects.create(
            user=timetable.created_by,
            message=f"Your timetable for {timetable.subject_name} has been {timetable.status.lower()}",
            timetable=timetable
        )

        # Send WebSocket notification - MODIFIED THIS PART
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{timetable.created_by.id}",
            {
                "type": "send.notification",  # Changed to use dot notation
                "id": notification.id,
                "title": "Timetable Update",
                "message": notification.message,
                "timetable_id": timetable.id,
                "created_at": notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # More standard format
                "is_read": False
            }
        )

        return Response(TimetableSerializer(timetable).data)

class SemesterListView(APIView):
    def get(self, request):
        course_id = request.query_params.get('course_id')
        
        queryset = Semester.objects.all()
        
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                queryset = queryset.filter(course=course)
            except Course.DoesNotExist:
                return Response(
                    {'error': 'Invalid course ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        semesters = queryset.select_related('course', 'university').values(
            'id',
            'name',
            'start_date',
            'end_date',
            'course_id',
            'course__name',
            'course__code',
            'university_id',
            'university__name'
        )
        
        return Response(list(semesters))
    
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'LECTURE':
            return Task.objects.filter(lecturer=user)
        elif user.user_type == 'MONITOR':
            return Task.objects.filter(monitor=user)
        return Task.objects.none()
    
    def perform_create(self, serializer):
        if self.request.user.user_type == 'LECTURE':
            serializer.save(lecturer=self.request.user)

# ==============================================
# USER PROFILE VIEWS
# ==============================================

class UserProfileView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            if 'password' in request.data:
                user.set_password(request.data['password'])
                user.save()
                serializer = UserSerializer(user)
                return Response(serializer.data)
            
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==============================================
# LIST VIEWS
# ==============================================

class LectureListView(APIView):
    def get(self, request):
        lectures = User.objects.filter(user_type='LECTURE').values(
            'id', 
            'first_name', 
            'last_name',
            'email'
        )
        return Response(list(lectures))

class CourseListView(APIView):
    def get(self, request):
        courses = Course.objects.all().values(
            'id',
            'name',
            'code',
            'university__name'
        )
        return Response(list(courses))

class UniversityListView(APIView):
    def get(self, request):
        universities = University.objects.all().values(
            'id',
            'name',
            'location',
            'established_year'
        )
        return Response(list(universities))

class MonitorListView(APIView):
    def get(self, request):
        monitors = User.objects.filter(user_type='MONITOR').values(
            'id',
            'first_name',
            'last_name',
            'email',
            'registration_number'
        )
        return Response(list(monitors))

# ==============================================
# DETAIL VIEWS
# ==============================================

class UniversityDetailView(APIView):
    def get(self, request, pk):
        try:
            university = University.objects.get(pk=pk)
            serializer = UniversitySerializer(university)
            return Response(serializer.data)
        except University.DoesNotExist:
            return Response(
                {'error': 'University not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class CourseDetailView(APIView):
    def get(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
            serializer = CourseSerializer(course)
            return Response(serializer.data)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class SemesterDetailView(APIView):
    def get(self, request, pk):
        try:
            semester = Semester.objects.get(pk=pk)
            serializer = SemesterSerializer(semester)
            return Response(serializer.data)
        except Semester.DoesNotExist:
            return Response(
                {'error': 'Semester not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class LectureDetailView(APIView):
    def get(self, request, pk):
        try:
            lecture = User.objects.get(pk=pk, user_type='LECTURE')
            serializer = UserSerializer(lecture)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Lecture not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class MonitorDetailView(APIView):
    def get(self, request, pk):
        try:
            monitor = User.objects.get(pk=pk, user_type='MONITOR')
            serializer = UserSerializer(monitor)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Monitor not found'},
                status=status.HTTP_404_NOT_FOUND
            )

# ==============================================
# TIMETABLE RELATED VIEWS
# ==============================================

class TimetableByCourseView(APIView):
    def get(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
            timetables = Timetable.objects.filter(course=course).select_related(
                'lecturer', 'created_by', 'semester'
            ).order_by('day', 'start_time')
            
            serializer = TimetableSerializer(timetables, many=True)
            return Response(serializer.data)
            
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class TimetableBySemesterView(APIView):
    def get(self, request, semester_id):
        try:
            semester = Semester.objects.get(pk=semester_id)
            timetables = Timetable.objects.filter(semester=semester).select_related(
                'lecturer', 'created_by', 'course'
            ).order_by('day', 'start_time')
            
            serializer = TimetableSerializer(timetables, many=True)
            return Response(serializer.data)
            
        except Semester.DoesNotExist:
            return Response(
                {'error': 'Semester not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class TimetableByDayView(APIView):
    def get(self, request, day):
        day = day.upper()
        if day not in dict(Timetable.DAY_CHOICES):
            return Response(
                {'error': f'Invalid day. Must be one of: {", ".join(dict(Timetable.DAY_CHOICES).keys())}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        timetables = Timetable.objects.filter(day=day).select_related(
            'lecturer', 'created_by', 'course', 'semester'
        ).order_by('start_time')
        
        serializer = TimetableSerializer(timetables, many=True)
        return Response(serializer.data)