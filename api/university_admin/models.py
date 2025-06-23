from django.db import models
from django.contrib.auth.models import AbstractUser

class University(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Course(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Semester(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.course} - {self.name}"

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('LECTURE', 'Lecture'),
        ('MONITOR', 'Monitor'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    assigned_course = models.ForeignKey(Course, on_delete=models.SET_NULL, blank=True, null=True)
    assigned_semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Add these to resolve the groups and permissions conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='timetable_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='timetable_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    class Meta:
        swappable = 'AUTH_USER_MODEL'
    
    def __str__(self):
        if self.user_type == 'MONITOR':
            return f"{self.registration_number} - {self.get_full_name()}"
        return self.email

class Timetable(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    DAY_CHOICES = (
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
        ('FRIDAY', 'Friday'),
    )
    
    subject_code = models.CharField(max_length=50)
    subject_name = models.CharField(max_length=200)
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'LECTURE'})
    venue = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    color_code = models.CharField(max_length=7, default='#FFFFFF')  # Hex color
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    cancellation_note = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_timetables')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.subject_code} - {self.day} {self.start_time}-{self.end_time}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, blank=True, null=True, related_name='timetable_notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} - {self.message[:50]}"

class Task(models.Model):
    lecturer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 'LECTURE'},
        related_name='lecturer_tasks'
    )
    monitor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'MONITOR'},
        related_name='monitor_tasks'
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Task from {self.lecturer} to {self.monitor}"