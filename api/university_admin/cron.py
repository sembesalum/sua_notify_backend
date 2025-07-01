from django.utils import timezone
from datetime import timedelta
from .models import Timetable
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_timetable_reminders():
    now = timezone.now()
    reminder_time = now + timedelta(minutes=5)
    
    # Get timetables starting within the next 5 minutes (since cron runs every 5 minutes)
    upcoming_timetables = Timetable.objects.filter(
        start_time__gte=(now.time()),
        start_time__lte=(reminder_time.time()),
        day=now.strftime('%A').upper(),  # Current day in uppercase (e.g., "MONDAY")
    )
    
    channel_layer = get_channel_layer()
    
    for timetable in upcoming_timetables:
        # Send to lecturer
        async_to_sync(channel_layer.group_send)(
            f"user_{timetable.lecturer.id}",
            {
                "type": "send.notification",
                "id": -1,  # Special ID for system notifications
                "title": "Class Reminder",
                "message": f"You have {timetable.subject_name} in 5 minutes at {timetable.venue}",
                "timetable_id": timetable.id,
                "created_at": now.strftime('%Y-%m-%d %H:%M:%S'),
                "is_read": False
            }
        )
        
        # Also send to CR (creator)
        if timetable.lecturer != timetable.created_by:
            # Send a status update reminder to CR (creator) from lecturer
            async_to_sync(channel_layer.group_send)(
                f"user_{timetable.created_by.id}",
                {
                    "type": "send.notification",
                    "id": -2,
                    "title": "Status Update Reminder",
                    "message": f"Reminder: Please update the status for {timetable.subject_name} class with {timetable.lecturer.get_full_name()}",
                    "timetable_id": timetable.id,
                    "created_at": now.strftime('%Y-%m-%d %H:%M:%S'),
                    "is_read": False
                }
            )