import uuid

from django.conf import settings
from django.db import models


class School(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name='school_admin',
                              blank=False,
                              null=True
                              )
    pupils = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='pupils', blank=True)