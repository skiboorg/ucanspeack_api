import uuid

from django.conf import settings
from django.db import models
from pytils.translit import slugify

class School(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(verbose_name="Slug урока", max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to="school/images", null=True, blank=True)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name='school_admin',
                              blank=False,
                              null=True
                              )
    pupils = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='pupils', blank=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(School, self).save(*args, **kwargs)