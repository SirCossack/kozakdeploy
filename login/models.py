from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class AppUser(AbstractUser):
    first_name = None
    last_name = None
    is_staff = None
    REQUIRED_FIELDS = []

    uid = models.BigIntegerField(primary_key=True, null=False)
    username = models.CharField(max_length=64)
    email = models.EmailField()
    is_authenticated = models.BooleanField(default=1)
    bot_active = models.BooleanField(default=0)

    class AppUserManager(models.Manager):
        def create_user(self, *args, **kwargs):
            user = AppUser(**kwargs)
            user.save()

    objects = AppUserManager()
