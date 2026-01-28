from rest_framework import serializers

from lesson.models import (
    Course, Level, Lesson, Module, ModuleBlock,
    Video, Phrase, LessonItem, DictionaryGroup, DictionaryItem, ModuleBlockDone, DictionaryItemFavorite,
    LessonItemFavoriteItem,OrthographyItem,OrthographyItemDone
)

class DictionaryItemSerializer(serializers.ModelSerializer):
    is_favorite = serializers.BooleanField(read_only=True)
    class Meta:
        model = DictionaryItem
        fields = ["id", "text_ru", "text_en", "sound","is_favorite","file"]



class LessonItemFavoriteItemSerializer(serializers.ModelSerializer):
    is_like = serializers.BooleanField(read_only=True)
    class Meta:
        model = LessonItem
        fields = ["id", "text_ru", "text_en", "sound","is_like"]

class DictionaryItemFavoriteSerializer(serializers.ModelSerializer):
    dictionary_item = DictionaryItemSerializer(many=False, read_only=True)

    class Meta:
        model = DictionaryItemFavorite
        fields = ['dictionary_item']

class DictionaryGroupSerializer(serializers.ModelSerializer):
    items = DictionaryItemSerializer(many=True, read_only=True)

    class Meta:
        model = DictionaryGroup
        fields = ["id", "title", "items"]


class PhraseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phrase
        fields = ["id", "start_time", "end_time", "text_en", "text_ru", "sound",'file']


class VideoSerializer(serializers.ModelSerializer):
    phrases = PhraseSerializer(many=True, read_only=True)
    file = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ["id", "video_src", "phrases", "file", "video_number"]

    def get_file(self, obj):
        request = self.context.get("request")
        print(request.build_absolute_uri(obj.file.url))
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class LessonItemSerializer(serializers.ModelSerializer):
    is_like = serializers.SerializerMethodField()

    class Meta:
        model = LessonItem
        fields = ["id", "text_ru", "text_en", "file","is_like"]

    def get_is_like(self, obj):
        return bool(getattr(obj, "user_favorites", []))


class ModuleBlockSerializer(serializers.ModelSerializer):
    videos = VideoSerializer(many=True, read_only=True)
    items = LessonItemSerializer(many=True, read_only=True)
    is_done = serializers.SerializerMethodField()

    class Meta:
        model = ModuleBlock
        fields = ["id", "sorting", "caption", "type3_content", "videos", "items","is_done","can_be_done"]

    def get_is_done(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False

        return ModuleBlockDone.objects.filter(
            user=request.user,
            module_block=obj
        ).exists()


class ModuleSerializer(serializers.ModelSerializer):
    blocks = ModuleBlockSerializer(many=True, read_only=True)
    lesson_mp3 = serializers.SerializerMethodField()
    is_done = serializers.BooleanField(read_only=True)
    module_dictionary_groups = DictionaryGroupSerializer(many=True, read_only=True)
    class Meta:
        model = Module
        fields = ["id", "title", "index", "url", "sorting", "blocks","lesson_mp3","is_done","module_dictionary_groups"]

    def get_lesson_mp3(self, obj):
        return obj.lesson.mp3


class ModuleShortSerializer(serializers.ModelSerializer):
    is_done = serializers.BooleanField(read_only=True)
    class Meta:
        model = Module
        fields = ["id", "title", "index", "url", "sorting","is_done"]

class OrthographyItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrthographyItem
        fields = ["id", "ru_text", "en_text", "order",]

class LessonSerializer(serializers.ModelSerializer):
    modules = ModuleShortSerializer(many=True, read_only=True)
    progress = serializers.IntegerField(read_only=True)
    is_done = serializers.BooleanField(read_only=True)
    dictionary_groups = DictionaryGroupSerializer(many=True, read_only=True)
    orthography_items = OrthographyItemSerializer(many=True, read_only=True)
    level_title = serializers.SerializerMethodField()
    course_title = serializers.SerializerMethodField()
    have_table = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id",
                  "title",
                  "slug",
                  "url",
                  "mp3",
                  "file",
                  "modules",
                  "progress",
                  "is_done",
                  "dictionary_groups",
                  "orthography_items",
                  "level_title",
                  "course_title",
                  "have_table",
                  "orthography_description",
                  "table_file"
                  ]

    def get_level_title(self, obj):
        return obj.level.title

    def get_course_title(self, obj):
        return obj.level.course.title

    def get_have_table(self, obj):
        return bool(obj.table)

class LessonShortSerializer(serializers.ModelSerializer):
    progress = serializers.IntegerField(read_only=True)
    is_done = serializers.BooleanField(read_only=True)
    class Meta:
        model = Lesson
        fields = ["id", "title", "slug","short_description","progress", "is_done",'is_free']


class LevelSerializer(serializers.ModelSerializer):
    lessons = LessonShortSerializer(many=True, read_only=True)
    course = serializers.SerializerMethodField()

    class Meta:
        model = Level
        fields = ["id", "title", "slug", "description", "course", "lessons"]

    def get_course(self, obj):
        return {
            "course_title": obj.course.title,
            "course_slug": obj.course.slug,
        }


class LevelShortSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    done_lessons_count = serializers.IntegerField(read_only=True)
    progress = serializers.IntegerField(read_only=True)  # аннотированное поле
    is_done = serializers.BooleanField(read_only=True)  # аннотированное поле

    class Meta:
        model = Level
        fields = ["id", "title", "slug", "description", "lessons_count", "progress",
                  "is_done","done_lessons_count","icon"]

    def get_lessons_count(self, obj):
        return getattr(obj, 'total_lessons', obj.lessons.count())


class CourseSerializer(serializers.ModelSerializer):
    levels = LevelShortSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "slug", "levels","cover",'bg_color']


