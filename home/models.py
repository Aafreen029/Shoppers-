from django.db import models
from django.contrib.auth.models import AbstractUser

from .manager import UserManager
# Create your models here.

class CustomUser(AbstractUser):

    email=models.EmailField(unique=True,blank=False)
    phone_number=models.CharField(unique=True)
    user_bio=models.CharField(max_length=50)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.first_name or self.email

    USERNAME_FIELD= 'email'
    REQUIRED_FIELDS=[]

    objects = UserManager()


