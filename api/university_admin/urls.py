from django.urls import path
from .views import (
    AdminDashboard, CourseListView, LectureListView, LectureTimetableByIdView, 
    MonitorTimetableByIdView, SemesterListView, TimetableStatusUpdateView, TimetableUpdateView, 
    UniversityCreateView, CourseCreateView, SemesterCreateView, LectureCreateView, 
    MonitorCreateView, MonitorLoginView, LectureLoginView, UserProfileView,
    TimetableViewSet, NotificationViewSet, TaskViewSet, TimetableCreateView, TimetableDeleteView,
    # Add the new views for edit/delete operations
    UniversityUpdateView, UniversityDeleteView,
    CourseUpdateView, CourseDeleteView,
    SemesterUpdateView, SemesterDeleteView,
    LectureUpdateView, LectureDeleteView,
    MonitorUpdateView, MonitorDeleteView
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'api/timetables', TimetableViewSet, basename='timetable')
router.register(r'api/notifications', NotificationViewSet, basename='notification')
router.register(r'api/tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', AdminDashboard.as_view(), name='admin_dashboard'),
    path('create-university/', UniversityCreateView.as_view(), name='create_university'),
    path('create-course/', CourseCreateView.as_view(), name='create_course'),
    path('create-semester/', SemesterCreateView.as_view(), name='create_semester'),
    path('create-lecture/', LectureCreateView.as_view(), name='create_lecture'),
    path('create-monitor/', MonitorCreateView.as_view(), name='create_monitor'),
    
    path('users/login/monitor/', MonitorLoginView.as_view(), name='monitor_login'),
    path('users/login/lecture/', LectureLoginView.as_view(), name='lecture_login'),
    
    path('users/profile/', UserProfileView.as_view(), name='user_profile'),
    
    path('lectures/', LectureListView.as_view(), name='lecture-list'),
    path('courses/', CourseListView.as_view(), name='course-list'),
    path('timetables/create/', TimetableCreateView.as_view(), name='timetable-create'),
    path('semesters/', SemesterListView.as_view(), name='semester-list'),
    path('monitor/<int:monitor_id>/timetables/', MonitorTimetableByIdView.as_view(), name='monitor-timetables-by-id'),
    path('lecture/<int:lecture_id>/timetables/', LectureTimetableByIdView.as_view(), name='lecture-timetables-by-id'),
    path('timetables/<int:timetable_id>/status/', TimetableStatusUpdateView.as_view(), name='timetable-status-update'),
    path('timetables/<int:pk>/edit/', TimetableUpdateView.as_view(), name='timetable-update'),
    path('timetables/<int:pk>/delete/', TimetableDeleteView.as_view(), name='timetable-delete'),
    
    path('universities/<int:pk>/edit/', UniversityUpdateView.as_view(), name='edit_university'),
    path('universities/<int:pk>/delete/', UniversityDeleteView.as_view(), name='delete_university'),
    
    path('courses/<int:pk>/edit/', CourseUpdateView.as_view(), name='edit_course'),
    path('courses/<int:pk>/delete/', CourseDeleteView.as_view(), name='delete_course'),
    
    path('semesters/<int:pk>/edit/', SemesterUpdateView.as_view(), name='edit_semester'),
    path('semesters/<int:pk>/delete/', SemesterDeleteView.as_view(), name='delete_semester'),
    
    path('lectures/<int:pk>/edit/', LectureUpdateView.as_view(), name='edit_lecture'),
    path('lectures/<int:pk>/delete/', LectureDeleteView.as_view(), name='delete_lecture'),
    
    path('monitors/<int:pk>/edit/', MonitorUpdateView.as_view(), name='edit_monitor'),
    path('monitors/<int:pk>/delete/', MonitorDeleteView.as_view(), name='delete_monitor'),
    
    *router.urls,
]