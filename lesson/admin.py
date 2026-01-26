from django.contrib import admin
from lesson.models import *
from django.utils.html import format_html
from django.urls import reverse

# --- Фразы (inline для видео) ---
class PhraseInline(admin.TabularInline):
    model = Phrase
    extra = 0
    fields = ("start_time", "end_time", "text_en", "text_ru", "sound")
    readonly_fields = ()
    verbose_name = "Фраза"
    verbose_name_plural = "Фразы"


# --- Видео (inline для блока модуля) ---
class VideoInline(admin.TabularInline):
    model = Video
    extra = 0
    fields = ("video_src",)
    inlines = [PhraseInline]
    verbose_name = "Видео"
    verbose_name_plural = "Видео"


# --- Элементы урока (inline для блока модуля) ---
class LessonItemInline(admin.TabularInline):
    model = LessonItem
    extra = 0
    fields = ("text_ru", "text_en", "sound")
    verbose_name = "Элемент урока"
    verbose_name_plural = "Элементы урока"


# --- Блоки модуля (inline для модуля) ---
class ModuleBlockInline(admin.StackedInline):
    model = ModuleBlock
    extra = 0
    fields = ("sorting", "caption", "type3_content")
    inlines = [VideoInline, LessonItemInline]
    verbose_name = "Блок модуля"
    verbose_name_plural = "Блоки модуля"

class OrthographyItemInline(admin.StackedInline):
    model = OrthographyItem
    extra = 0
    fields = ("order","ru_text", "en_text",)
    verbose_name = "Задание орфографии"
    verbose_name_plural = "Задания орфографии"


# --- Модули (inline для урока) ---
class ModuleInline(admin.StackedInline):
    model = Module
    extra = 0
    fields = ("index", "title",  "sorting")
    inlines = [ModuleBlockInline]
    verbose_name = "Модуль"
    verbose_name_plural = "Модули"


# --- Уроки (inline для уровня) ---
class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 0
    fields = ("title", "slug", "url", "mp3")
    inlines = [ModuleInline]
    verbose_name = "Урок"
    verbose_name_plural = "Уроки"


# --- Словарь (inline для урока) ---
class DictionaryItemInline(admin.TabularInline):
    model = DictionaryItem
    extra = 0
    fields = ("text_ru", "text_en","file")
    verbose_name = "Слово"
    verbose_name_plural = "Слова"


class DictionaryGroupInline(admin.StackedInline):
    model = DictionaryGroup
    extra = 0
    fields = ("title",)
    inlines = [DictionaryItemInline]
    verbose_name = "Группа словаря"
    verbose_name_plural = "Группы словаря"


# --- Уровни (inline для курса) ---
class LevelInline(admin.StackedInline):
    model = Level
    extra = 0
    fields = ("title", "slug", "description",)
    inlines = [LessonInline]
    verbose_name = "Уровень"
    verbose_name_plural = "Уровни"


# --- Админка Course ---
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    search_fields = ("title",)
    inlines = [LevelInline]


# --- Админка Level (для редактирования отдельно) ---
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("order_num","title", "course", "slug")
    search_fields = ("title", "course__title")
    list_filter = ("course",)


# --- Админка Lesson ---
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("order_num","title", "level", "slug",)
    search_fields = ("title", "level__title")
    list_filter = ("level",)
    inlines = [ModuleInline, DictionaryGroupInline,OrthographyItemInline]

#
# # --- Админка Module ---
# @admin.register(Module)
# class ModuleAdmin(admin.ModelAdmin):
#     list_display = ("title", "lesson", "index", "sorting", "url")
#     search_fields = ("title", "lesson__title")
#     list_filter = ("lesson",)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson_with_level", "index", "sorting",)
    search_fields = ("title", "lesson__title", "lesson__level__title")
    list_filter = ("lesson", "lesson__level")
    inlines = [ModuleBlockInline]

    @admin.display(description='Урок (Уровень)', ordering='lesson__title')
    def lesson_with_level(self, obj):
        if obj.lesson:
            # Ссылка на урок
            lesson_url = reverse('admin:lesson_lesson_change', args=[obj.lesson.id])

            # Ссылка на уровень
            if obj.lesson.level:
                level_url = reverse('admin:lesson_level_change', args=[obj.lesson.level.id])
                level_html = format_html('<a href="{}">{}</a>', level_url, obj.lesson.level.title)
            else:
                level_html = "Нет уровня"

            lesson_html = format_html('<a href="{}">{}</a>', lesson_url, obj.lesson.title)
            return format_html('{}<br><small>Уровень: {}</small>', lesson_html, level_html)
        return "-"


@admin.register(ModuleBlock)
class ModuleBlockAdmin(admin.ModelAdmin):
    list_display = ("id", "module", "sorting", "caption_preview", "lesson_info")
    list_filter = ("module__lesson", "module")
    search_fields = (
        "caption",
        "module__title",  # Поиск по названию модуля
        "module__lesson__title",  # Поиск по названию урока
        "module__lesson__level__title",  # Поиск по названию уровня
        "module__lesson__level__course__title",  # Поиск по названию курса
    )

    @admin.display(description='Превью текста')
    def caption_preview(self, obj):
        if obj.caption:
            return obj.caption[:100] + "..." if len(obj.caption) > 100 else obj.caption
        return "-"

    @admin.display(description='Урок → Модуль')
    def lesson_info(self, obj):
        if obj.module and obj.module.lesson:
            return f"{obj.module.lesson.title} → {obj.module.title}"
        return "-"

# --- Админка Video ---
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("id", "video_number")  # оставил правильный ForeignKey
    search_fields = ("video_number",)
    inlines = [PhraseInline]


# --- Админка Phrase ---
@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    list_display = ("text_en", "text_ru",)
    search_fields = ("text_en", "text_ru")


@admin.register(DictionaryGroup)
class DictionaryGroupAdmin(admin.ModelAdmin):
    list_display = ("order","title", "lesson", "module_info")
    search_fields = ("title", "lesson__title")
    list_filter = ("lesson",)
    inlines = [DictionaryItemInline]

    # Ключевое изменение: используем autocomplete_fields
    autocomplete_fields = ['module']

    @admin.display(description='Информация о блоке')
    def module_info(self, obj):
        if obj.module:
            lesson = obj.module.lesson
            module = obj.module
            return f"{lesson.title} → {module.title} → Блок {obj.module.sorting}"
        return "-"

@admin.register(ModuleBlockDone)
class ModuleBlockDoneAdmin(admin.ModelAdmin):
    list_display = ("id",)

@admin.register(LessonDone)
class LessonDoneAdmin(admin.ModelAdmin):
    list_display = ("id",)

@admin.register(DictionaryItemFavorite)
class DictionaryItemFavoriteAdmin(admin.ModelAdmin):
    list_display = ("id",)

@admin.register(LessonItemFavoriteItem)
class LessonItemFavoriteItemAdmin(admin.ModelAdmin):
    list_display = ("id",)