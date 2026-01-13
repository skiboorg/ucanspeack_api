from django.db import models
from django.utils.text import slugify
from django.conf import settings

class Course(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.FileField(upload_to='trainer/course_icons/', null=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Level(models.Model):
    course = models.ForeignKey(Course, related_name="levels", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    icon = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("course", "slug")
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class Topic(models.Model):
    level = models.ForeignKey(Level, related_name="topics", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    order_txt = models.CharField(max_length=255, blank=True, null=True)
    is_common = models.BooleanField('Обобщающий', default=False)

    class Meta:
        unique_together = ("level", "slug")
        ordering = ["order"]

    def __str__(self):
        return f"{self.level.name} - {self.name}"


class AudioFile(models.Model):
    topic = models.ForeignKey(Topic, related_name="audio_files", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    mp3 = models.URLField()
    description = models.TextField(blank=True, null=True)
    order = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='trainer/mp3', null=True, blank=True)
    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.topic.name} - {self.name}"


class Phrase(models.Model):
    topic = models.ForeignKey(Topic, related_name="phrases", on_delete=models.CASCADE)
    text_ru = models.TextField()
    text_en = models.TextField()
    sound = models.URLField(blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    file = models.FileField(upload_to='trainer/phrase', null=True, blank=True)
    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.text_ru} / {self.text_en}"


class PhraseFavorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,blank=True,null=True)
    phrase = models.ForeignKey(Phrase,on_delete=models.CASCADE,blank=True,null=True, related_name="trainer_phrase_favorites")