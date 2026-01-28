from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.db.models import Prefetch, Value, BooleanField
from django.db import transaction

from .models import Course, Level, Topic, Phrase, PhraseFavorite, TopicDone, LevelDone
from .serializers import (
    CourseSerializer,
    LevelSerializer,
    TopicListSerializer,
    TopicDetailSerializer,

    PhraseSerializer

)


class FavoriteListAPIView(ListAPIView):
    serializer_class = PhraseSerializer

    def get_queryset(self):
        return (
            Phrase.objects
            .filter(trainer_phrase_favorites__user=self.request.user)
            .annotate(is_like=Value(True, output_field=BooleanField()))
        )

# 1️⃣ Все курсы
class CourseListView(ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


# 2️⃣ Уровни по slug курса
class LevelListByCourseView(ListAPIView):
    serializer_class = LevelSerializer

    def get_queryset(self):
        course_slug = self.kwargs["course_slug"]
        return (
            Level.objects
            .filter(course__slug=course_slug)
            .select_related("course")
            .order_by("order_num")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # берём курс из первого уровня
        course = get_object_or_404(
            Course,
            slug=self.kwargs["course_slug"]
        )

        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "course": {
                "name": course.name,
            },
            "levels": serializer.data
        })


# 3️⃣ Топики по slug уровня (без аудио и фраз)
class TopicListByLevelView(ListAPIView):
    serializer_class = TopicListSerializer

    def get_queryset(self):
        level_slug = self.kwargs["level_slug"]
        return (
            Topic.objects
            .filter(level__slug=level_slug)
            .select_related("level__course")
            .order_by("order")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        level = get_object_or_404(
            Level.objects.select_related("course"),
            slug=self.kwargs["level_slug"]
        )

        course = level.course

        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "course": {
                "name": course.name,
            },
            "level": {
                "name": level.name,
            },
            "topics": serializer.data
        })


# 4️⃣ Один топик по slug (с аудио и фразами)
class TopicDetailView(RetrieveAPIView):
    serializer_class = TopicDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        user = self.request.user

        favorites_qs = PhraseFavorite.objects.filter(user=user)

        return (
            Topic.objects
            .select_related("level__course")
            .prefetch_related(
                "audio_files",
                Prefetch("phrases", queryset=Phrase.objects.prefetch_related(
                    Prefetch(
                        "trainer_phrase_favorites",
                        queryset=favorites_qs,
                        to_attr="user_favorites"
                    )
                ))
            )
        )

    def retrieve(self, request, *args, **kwargs):
        topic = self.get_object()

        level = topic.level
        course = level.course

        serializer = self.get_serializer(topic)

        return Response({
            "course": {
                "name": course.name,
            },
            "level": {
                "name": level.name,
            },
            "topic": serializer.data
        })


class ToggleFavoriteAPIView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user
        obj, created = PhraseFavorite.objects.get_or_create(
            user=user,
            phrase_id=request.data["id"]
        )
        if not created:
            obj.delete()
        return Response(status=200)


class TopicDoneAPIView(APIView):

    def post(self, request):
        topic_id = request.data["topic_id"]
        try:
            topic = Topic.objects.get(id=topic_id)
        except Topic.DoesNotExist:
            return Response(
                {"error": "Topic not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            # Создаем TopicDone (get_or_create предотвращает дубликаты)
            topic_done, created = TopicDone.objects.get_or_create(
                user=request.user,
                topic=topic
            )

            if not created:
                return Response(
                    {"message": "Topic already marked as done"},
                    status=status.HTTP_200_OK
                )

            # Проверяем, выполнены ли все топики в уровне
            level = topic.level
            total_topics = level.topics.count()
            print('total_topics', total_topics)
            completed_topics = TopicDone.objects.filter(
                user=request.user,
                topic__level=level
            ).count()
            print('completed_topics', completed_topics)

            level_completed = False
            if total_topics > 0 and total_topics == completed_topics:
                # Все топики выполнены - создаем LevelDone
                LevelDone.objects.get_or_create(
                    user=request.user,
                    level=level
                )
                level_completed = True

            return Response(
                {
                    "message": "Topic marked as done",
                    "level_completed": level_completed,
                    "progress": {
                        "completed_topics": completed_topics,
                        "total_topics": total_topics
                    }
                },
                status=status.HTTP_201_CREATED
            )