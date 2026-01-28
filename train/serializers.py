from rest_framework import serializers
from .models import Course, Level, Topic, AudioFile, Phrase, TopicDone, LevelDone


class CourseSerializer(serializers.ModelSerializer):
    completed_levels = serializers.SerializerMethodField()
    total_levels = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "name",
            "slug",
            "description",
            "icon",
            "completed_levels",
            "total_levels",
            "progress_percentage",
        )

    def get_total_levels(self, obj):
        return obj.levels.count()

    def get_completed_levels(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LevelDone.objects.filter(
                user=request.user,
                level__course=obj
            ).count()
        return 0

    def get_progress_percentage(self, obj):
        total = self.get_total_levels(obj)
        if total == 0:
            return 0
        completed = self.get_completed_levels(obj)
        return round((completed / total) * 100, 2)


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "order",
            "url",
            "icon",
        )


# ❗ Топики без аудио и фраз
class TopicListSerializer(serializers.ModelSerializer):
    is_done = serializers.SerializerMethodField()
    class Meta:
        model = Topic
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "order",
            "order_txt",
            "url",
            "is_common",
            "is_done"
        )
    def get_is_done(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return TopicDone.objects.filter(user=request.user, topic=obj).exists()
        return False


class AudioFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFile
        fields = (
            "id",
            "name",
            "slug",
            "mp3",
            "file",
            "description",
            "order",
        )


class PhraseSerializer(serializers.ModelSerializer):
    is_like = serializers.SerializerMethodField()
    class Meta:
        model = Phrase
        fields = (
            "id",
            "text_ru",
            "text_en",
            "sound",
            "order",
            "file",
            "is_like",
        )

    def get_is_like(self, obj):
        return bool(getattr(obj, "user_favorites", []))


# ✅ Один топик со всем содержимым
class TopicDetailSerializer(serializers.ModelSerializer):
    audio_files = AudioFileSerializer(many=True)
    phrases = PhraseSerializer(many=True)
    is_done = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "order",
            "order_txt",
            "url",
            "audio_files",
            "phrases",
            "is_done",
        )

    def get_is_done(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return TopicDone.objects.filter(user=request.user, topic=obj).exists()
        return False
