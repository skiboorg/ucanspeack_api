from django.db import models
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field

class Course(models.Model):
    """Курс"""
    title = models.CharField(max_length=255, verbose_name="Название курса")
    slug = models.SlugField(verbose_name="Slug курса",max_length=255)

    def __str__(self):
        return self.title


class Level(models.Model):
    """Уровень курса (Beginner, Intermediate, Advanced...)"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="levels", verbose_name="Курс")
    title = models.CharField(max_length=255, verbose_name="Название уровня")
    slug = models.SlugField(verbose_name="Slug уровня",max_length=255)
    description = models.TextField(null=True, blank=True, verbose_name="Описание уровня")
    url = models.URLField(max_length=500, verbose_name="URL уровня")

    def __str__(self):
        return f"{self.course.title} → {self.title}"


class Lesson(models.Model):
    """Урок внутри уровня"""
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="lessons", verbose_name="Уровень")
    title = models.CharField(max_length=255, verbose_name="Название урока")
    short_description = models.CharField(max_length=255, verbose_name="Описание урока", null=True, blank=True)
    slug = models.SlugField(verbose_name="Slug урока",max_length=255)
    url = models.URLField(max_length=500, verbose_name="URL урока")
    mp3 = models.URLField(null=True, blank=True, verbose_name="Аудио MP3 урока")

    def __str__(self):
        return f"{self.level.title} → {self.title}"




class Module(models.Model):
    """Модуль внутри урока"""

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="modules", verbose_name="Урок")
    title = models.CharField(max_length=255, verbose_name="Название модуля")
    index = models.CharField(max_length=20, null=True, blank=True, verbose_name="Индекс модуля")
    url = models.URLField(max_length=500, null=True, blank=True, verbose_name="URL модуля")
    sorting = models.IntegerField(null=True, blank=True, verbose_name="Порядок отображения модуля")

    def __str__(self):
        return f"{self.lesson.title} → {self.title}"
    def save(self, *args, **kwargs):
        if self.index:
            try:
                # если index = "10" → sorting = 10
                self.sorting = int(self.index)
            except ValueError:
                # если index = "A1", "1.2", "01a" → None
                self.sorting = None
        else:
            self.sorting = None

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['sorting']

class ModuleBlock(models.Model):
    """Блок контента внутри модуля"""
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="blocks", verbose_name="Модуль")
    sorting = models.IntegerField(null=True, blank=True, verbose_name="Сортировка блока")
    caption = CKEditor5Field(null=True, blank=True, verbose_name="Текст/описание блока")
    type3_content = CKEditor5Field(blank=True, verbose_name="HTML контент блока (type3)")
    #type3_content = models.JSONField(default=list, blank=True, verbose_name="HTML контент блока (type3)")

    def __str__(self):
        return f"Блок {self.sorting} модуля {self.module.title}"

    class Meta:
        ordering = ['sorting']


class LessonItem(models.Model):
    """Фразы или элементы внутри блока"""
    block = models.ForeignKey(ModuleBlock, on_delete=models.CASCADE,null=True, blank=True, related_name="items", verbose_name="Блок")
    text_ru = models.TextField(null=True, blank=True, verbose_name="Текст на русском")
    text_en = models.TextField(null=True, blank=True, verbose_name="Текст на английском")
    sound = models.URLField(null=True, blank=True, verbose_name="Ссылка на аудио")

    def __str__(self):
        return self.text_en or self.text_ru or "Элемент урока"


class Video(models.Model):
    """Видео внутри блока"""
    block = models.ForeignKey(ModuleBlock, on_delete=models.CASCADE,null=True, blank=True, related_name="videos", verbose_name="Блок")
    video_src = models.URLField(verbose_name="Ссылка на видео",null=True, blank=True,)

    def __str__(self):
        return self.video_src


class Phrase(models.Model):
    """Фразы из видео"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="phrases", verbose_name="Видео")
    start_time = models.CharField(max_length=20, null=True, blank=True, verbose_name="Время начала")
    end_time = models.CharField(max_length=20, null=True, blank=True, verbose_name="Время конца")
    text_en = models.TextField(null=True, blank=True, verbose_name="Текст на английском")
    text_ru = models.TextField(null=True, blank=True, verbose_name="Текст на русском")
    sound = models.URLField(null=True, blank=True, verbose_name="Ссылка на аудио")

    def __str__(self):
        return self.text_en or self.text_ru or "Фраза видео"


class DictionaryGroup(models.Model):
    """Группа слов в словаре урока"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="dictionary_groups", verbose_name="Урок")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="module_dictionary_groups",
                                     verbose_name="Блок модуля", blank=True, null=True)
    title = models.CharField(max_length=255, verbose_name="Название группы")

    def __str__(self):
        return self.title


class DictionaryItem(models.Model):
    """Элемент словаря"""
    group = models.ForeignKey(DictionaryGroup, on_delete=models.CASCADE, related_name="items", verbose_name="Группа слов")
    text_ru = models.TextField(null=True, blank=True, verbose_name="Текст на русском")
    text_en = models.TextField(null=True, blank=True, verbose_name="Текст на английском")
    sound = models.CharField(max_length=255, null=True, blank=True, verbose_name="Ссылка на аудио")

    def __str__(self):
        return self.text_en or self.text_ru or "Элемент словаря"





class ModuleBlockDone(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,blank=True,null=True)
    module_block = models.ForeignKey('ModuleBlock',on_delete=models.CASCADE,blank=True,null=True)

class LessonDone(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,blank=True,null=True)
    lesson = models.ForeignKey('Lesson',on_delete=models.CASCADE,blank=True,null=True)

class DictionaryItemFavorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,blank=True,null=True)
    dictionary_item = models.ForeignKey(DictionaryItem,on_delete=models.CASCADE,blank=True,null=True)


class LessonItemFavoriteItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,blank=True,null=True)
    lesson_item = models.ForeignKey(LessonItem,on_delete=models.CASCADE,blank=True,null=True, related_name="lesson_item_favorites")