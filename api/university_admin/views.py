from datetime import datetime
import logging
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login
from rest_framework import viewsets, status
from rest_framework.response import Response
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
# Admin Views
class AdminDashboard(View):
    template_name = 'timetable/admin_dashboard.html'
    
    def get(self, request):
        universities = University.objects.all().order_by('-created_at')[:5]
        courses = Course.objects.all().order_by('-created_at')[:5]
        lectures = User.objects.filter(user_type='LECTURE').order_by('-date_joined')[:5]
        monitors = User.objects.filter(user_type='MONITOR').order_by('-date_joined')[:5]
        
        context = {
            'universities': universities,
            'courses': courses,
            'lectures': lectures,
            'monitors': monitors,
        }
        return render(request, self.template_name, context)

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

# Authentication Views
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
# API Views (ViewSets)


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
        # Extract required user IDs from request
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
        
        # Prepare data for creation
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
        
        # Verify the timetable belongs to this lecture
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
        
        # Create notification for monitor
        Notification.objects.create(
            user=timetable.created_by,
            message=f"Your timetable for {timetable.subject_name} has been {timetable.status.lower()}",
            timetable=timetable
        )
        
        return Response({'status': 'success'})
    
    


class TimetableCreateView(APIView):
    def _parse_time(self, time_str):
        """Parse various time formats into time object"""
        if isinstance(time_str, time):  # Already a time object
            return time_str
            
        time_str = str(time_str).strip()
        
        # Try common time formats
        for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M%p'):
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
                
        # Try formats without seconds
        if re.match(r'^\d{1,2}:\d{2}$', time_str):
            try:
                return datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                pass
                
        # Try 12-hour formats
        if re.match(r'^\d{1,2}:\d{2}\s*[ap]m$', time_str.lower()):
            try:
                return datetime.strptime(time_str, '%I:%M %p').time()
            except ValueError:
                pass
                
        raise ValueError(f"Invalid time format: {time_str}. Accepted formats: HH:MM:SS, HH:MM, H:MM AM/PM")

    def post(self, request):
        errors = {}
        
        # Validate required fields
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

        # Parse and validate times if they exist
        start_time = end_time = None
        if 'start_time' in request.data and 'end_time' in request.data:
            try:
                start_time = self._parse_time(request.data['start_time'])
                end_time = self._parse_time(request.data['end_time'])
                
                if end_time <= start_time:
                    errors['time'] = 'End time must be after start time'
            except ValueError as e:
                errors['time'] = str(e)

        # Validate day
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

            # Create the timetable instance directly to ensure created_by is set
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
                created_by=monitor,  # Directly set the user instance
                status='PENDING'
            )
            timetable.save()

            # Use serializer only for response, not creation
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

class TimetableView(ListAPIView):
    serializer_class = TimetableSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'day', 'course', 'semester']
    
    def get_queryset(self):
        queryset = Timetable.objects.all().select_related(
            'lecturer', 'created_by', 'course', 'semester'
        ).order_by('day', 'start_time')
        
        # Get status from query parameters
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status.upper())
        
        return queryset
    
class MonitorTimetableByIdView(APIView):
    """
    API endpoint that allows monitors to view their created timetables by ID only
    No permission checks, just ID verification
    """
    
    def get(self, request, monitor_id):
        try:
            # Verify the monitor exists (but don't check permissions)
            User.objects.get(id=monitor_id, user_type='MONITOR')
            
            # Get all timetables created by this monitor
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
    """
    API endpoint that allows lecturers to view their assigned timetables by ID only
    No permission checks, just ID verification
    """
    
    def get(self, request, lecture_id):
        try:
            # Verify the lecture exists (but don't check permissions)
            User.objects.get(id=lecture_id, user_type='LECTURE')
            
            # Get all timetables assigned to this lecturer
            timetables = Timetable.objects.filter(
                lecturer_id=lecture_id
            ).select_related(
                'created_by', 'course', 'semester'
            ).order_by('day', 'start_time')  # Ordered by day and time for better display
            
            serializer = TimetableSerializer(timetables, many=True)
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Lecturer with this ID does not exist'},
                status=status.HTTP_404_NOT_FOUND
            )
    
class TimetableStatusUpdateView(APIView):
    """
    API endpoint to update timetable status
    - Only the assigned lecturer can update the status
    - Requires lecturer_id for verification
    - Allows changing to CONFIRMED or CANCELLED
    - Requires cancellation note when cancelling
    """
    
    def patch(self, request, timetable_id):
        try:
            timetable = Timetable.objects.get(id=timetable_id)
        except Timetable.DoesNotExist:
            return Response(
                {'error': 'Timetable not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify lecturer exists and matches timetable's lecturer
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

        # Update the timetable
        timetable.status = serializer.validated_data['status']
        if timetable.status == 'CANCELLED':
            timetable.cancellation_note = serializer.validated_data.get('cancellation_note', '')
        
        timetable.save()

        # Create notification for the monitor who created this timetable
        Notification.objects.create(
            user=timetable.created_by,
            message=f"Your timetable for {timetable.subject_name} has been {timetable.status.lower()}",
            timetable=timetable
        )

        return Response(TimetableSerializer(timetable).data)

class SemesterListView(APIView):
    def get(self, request):
        # Optional course_id filter
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

# User Profile View
class UserProfileView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Handle password separately
            if 'password' in request.data:
                user.set_password(request.data['password'])
                user.save()
                # Return the same serializer but without password field
                serializer = UserSerializer(user)
                return Response(serializer.data)
            
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    # views.py
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