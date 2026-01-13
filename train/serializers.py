from rest_framework import serializers
from .models import Course, Level, Topic, AudioFile, Phrase


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("name", "slug", "description","icon")


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
        )


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
        )
