from django.contrib import admin
from .models import Course, Level, Topic, AudioFile, Phrase, PhraseFavorite

class AudioFileInline(admin.TabularInline):
    model = AudioFile
    extra = 0


class PhraseInline(admin.TabularInline):
    model = Phrase
    extra = 0


class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "order")
    inlines = [AudioFileInline, PhraseInline]


class LevelAdmin(admin.ModelAdmin):
    list_display = ("order_num","name", "course", "order")


admin.site.register(Course)
admin.site.register(Level, LevelAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(PhraseFavorite)
