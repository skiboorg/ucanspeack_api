import uuid
from django.conf import settings
from django.db import models

class UserToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=64, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Токен авторизации"
        verbose_name_plural = "Токены авторизации"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = uuid.uuid4().hex
        super().save(*args, **kwargs)
