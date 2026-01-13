import uuid

from django.conf import settings
from django.db import models


class School(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    pupils = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='pupils', blank=True)