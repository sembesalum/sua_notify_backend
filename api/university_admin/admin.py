from django.db import models
from django.contrib.auth.models import AbstractUser

class AdminUser(AbstractUser):
    is_admin = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'

    def __str__(self):
        return self.username