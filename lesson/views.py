from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from .models import *
from .serializers import *
from rest_framework.decorators import action

from django.db.models import Count, Q, F, Case, When, Value, IntegerField, BooleanField, ExpressionWrapper, Prefetch, Exists, OuterRef


class DictionaryItemFavoriteListAPIView(generics.ListAPIView):
    serializer_class = DictionaryItemSerializer

    def get_queryset(self):
        return (
            DictionaryItem.objects
            .filter(dictionaryitemfavorite__user=self.request.user)
            .annotate(is_favorite=Value(True, output_field=BooleanField()))
        )

class LessonItemFavoriteListAPIView(generics.ListAPIView):
    serializer_class = LessonItemFavoriteItemSerializer

    def get_queryset(self):
        return (
            LessonItem.objects
            .filter(lesson_item_favorites__user=self.request.user)
            .annotate(is_like=Value(True, output_field=BooleanField()))
        )

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user

        # Сначала аннотируем уровни с количеством выполненных уроков
        levels_qs = Level.objects.annotate(
            total_lessons=Count('lessons', distinct=True),
            done_lessons_count=Count(
                'lessons__lessondone',
                filter=Q(lessons__lessondone__user=user),
                distinct=True
            ),
            progress=Case(
                When(total_lessons=0, then=Value(0)),
                default=ExpressionWrapper(
                    F('done_lessons_count') * 100 / F('total_lessons'),
                    output_field=IntegerField()
                ),
                output_field=IntegerField()
            ),
            is_done=Case(
                When(total_lessons=0, then=Value(False)),
                When(total_lessons=F('done_lessons_count'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by("order_num")

        # Теперь аннотируем курсы с количеством выполненных уроков
        courses = Course.objects.annotate(
            done_lessons_count=Count(
                'levels__lessons__lessondone',
                filter=Q(levels__lessons__lessondone__user=user),
                distinct=True
            ),
            total_lessons=Count('levels__lessons', distinct=True),
            lessons_progress=Case(
                When(total_lessons=0, then=Value(0)),
                default=ExpressionWrapper(
                    F('done_lessons_count') * 100 / F('total_lessons'),
                    output_field=IntegerField()
                ),
                output_field=IntegerField()
            )
        ).prefetch_related(
            Prefetch('levels', queryset=levels_qs)
        )

        return courses




class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user

        # Аннотируем уроки с прогрессом
        lessons_qs = Lesson.objects.annotate(
            total_blocks=Count('modules__blocks', distinct=True),
            done_blocks=Count(
                'modules__blocks__moduleblockdone',
                filter=Q(modules__blocks__moduleblockdone__user=user),
                distinct=True
            ),
        ).annotate(
            progress=Case(
                When(total_blocks=0, then=Value(0)),
                default=ExpressionWrapper(
                    F('done_blocks') * 100 / F('total_blocks'),
                    output_field=IntegerField()
                ),
                output_field=IntegerField()
            ),
            is_done=Case(
                When(total_blocks=0, then=Value(False)),
                When(total_blocks=F('done_blocks'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('order_num')

        # Предзагрузка уроков с прогрессом
        levels = Level.objects.prefetch_related(
            Prefetch('lessons', queryset=lessons_qs)
        )

        # Теперь считаем прогресс уровня
        # total_lessons = общее кол-во уроков
        # done_lessons = кол-во уроков, где is_done=True
        levels = levels.annotate(
            total_lessons=Count('lessons', distinct=True),
            done_lessons=Count('lessons', filter=Q(lessons__modules__blocks__moduleblockdone__user=user),
                               distinct=True),
        ).annotate(
            progress=Case(
                When(total_lessons=0, then=Value(0)),
                default=ExpressionWrapper(
                    F('done_lessons') * 100 / F('total_lessons'),
                    output_field=IntegerField()
                ),
                output_field=IntegerField()
            ),
            is_done=Case(
                When(total_lessons=0, then=Value(False)),
                When(total_lessons=F('done_lessons'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        )

        return levels

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    lookup_field = 'slug'

    @action(detail=True, methods=['get'])
    def get_table(self, request, slug=None):
        """Возвращает HTML таблицы урока"""
        lesson = self.get_object()
        return Response({
            "slug": lesson.slug,
            "table": lesson.table
        })

    @action(detail=True, methods=['get'])
    def videos(self, request, slug=None):
        """Все видео урока с фразами"""
        lesson = self.get_object()
        all_videos = []

        # Проходим по модулям → блокам → видео
        for module in lesson.modules.all():
            for block in module.blocks.all():
                for video in block.videos.all():
                    all_videos.append(video)

        serializer = VideoSerializer(all_videos, many=True, context={"request": request})
        return Response(serializer.data)

    def get_queryset(self):
        print('asd')
        user = self.request.user

        # ---------- DictionaryItem queryset ----------
        dictionary_items_qs = DictionaryItem.objects.all()

        if user.is_authenticated:
            favorites = DictionaryItemFavorite.objects.filter(
                user=user,
                dictionary_item=OuterRef("pk")
            )
            dictionary_items_qs = dictionary_items_qs.annotate(
                is_favorite=Exists(favorites)
            )
        else:
            dictionary_items_qs = dictionary_items_qs.annotate(
                is_favorite=Value(False, output_field=BooleanField())
            )

        # ---------- Modules queryset ----------
        modules_qs = Module.objects.annotate(
            total_blocks=Count('blocks', distinct=True),
            done_blocks=Count(
                'blocks__moduleblockdone',
                filter=Q(blocks__moduleblockdone__user=user),
                distinct=True
            )
        ).annotate(
            is_done=Case(
                When(total_blocks=0, then=Value(False)),
                When(total_blocks=F('done_blocks'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('sorting')

        # ---------- Lessons queryset ----------
        lessons_qs = Lesson.objects.annotate(
            total_blocks=Count('modules__blocks', distinct=True),
            done_blocks=Count(
                'modules__blocks__moduleblockdone',
                filter=Q(modules__blocks__moduleblockdone__user=user),
                distinct=True
            )
        ).annotate(
            progress=Case(
                When(total_blocks=0, then=Value(0)),
                default=F('done_blocks') * 100 / F('total_blocks'),
                output_field=IntegerField()
            ),
            is_done=Case(
                When(total_blocks=0, then=Value(False)),
                When(total_blocks=F('done_blocks'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).prefetch_related(
            Prefetch('modules', queryset=modules_qs),
            Prefetch(
                'dictionary_groups__items',
                queryset=dictionary_items_qs
            )
        )

        # for lesson in lessons_qs:
        #     for module in lesson.modules.all():
        #         for block in module.blocks.all():
        #             if not block.can_be_done:
        #                 ModuleBlockDone.objects.get_or_create(
        #                     user=user,
        #                     module_block=block,
        #                 )

        return lessons_qs


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        module = self.get_object()

        user = request.user

        module_id = module.id
        lesson_slug = module.lesson.slug
        level_slug = module.lesson.level.slug
        course_slug = module.lesson.level.course.slug

        last_url= f'/courses/{course_slug}/{level_slug}/{lesson_slug}?m_id={module_id}'
        user.last_lesson_url = last_url
        user.save(update_fields=['last_lesson_url'])

        serializer = self.get_serializer(
            module,
            context={"request": request}
        )


        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user

        # queryset для DictionaryItem
        dictionary_items_qs = DictionaryItem.objects.all()

        if user.is_authenticated:
            favorites = DictionaryItemFavorite.objects.filter(
                user=user,
                dictionary_item=OuterRef("pk")
            )
            dictionary_items_qs = dictionary_items_qs.annotate(
                is_favorite=Exists(favorites)
            )
        else:
            dictionary_items_qs = dictionary_items_qs.annotate(
                is_favorite=Value(False, output_field=BooleanField())
            )

        # LessonItem favorites
        lesson_item_favorites_qs = LessonItemFavoriteItem.objects.none()

        if user.is_authenticated:
            lesson_item_favorites_qs = LessonItemFavoriteItem.objects.filter(user=user)

        return (
            Module.objects
            .annotate(
                total_blocks=Count('blocks', distinct=True),

                done_blocks=Count(
                    'blocks__moduleblockdone',
                    filter=Q(blocks__moduleblockdone__user=user),
                    distinct=True
                ),
            )
            .annotate(
                is_done=Case(
                    When(
                        total_blocks=F('done_blocks'),
                        total_blocks__gt=0,
                        then=True
                    ),
                    default=False,
                    output_field=BooleanField()
                )
            )
            .prefetch_related(
                Prefetch(
                    "module_dictionary_groups__items",
                    queryset=dictionary_items_qs
                ),
                Prefetch(
                    "blocks__items__lesson_item_favorites",
                    queryset=lesson_item_favorites_qs,
                    to_attr="user_favorites"
                )
            )
        )

    @action(detail=False, methods=['post'], url_path='toggle_favorite')
    def toggle_favorite(self, request, id=None):
        user = request.user
        lesson_item_id = request.data.get('id')
        obj, created = LessonItemFavoriteItem.objects.get_or_create(
            user=user,
            lesson_item_id=lesson_item_id
        )
        if not created:
            obj.delete()
        return Response(status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'], url_path='toggle_block')
    def toggle_block(self, request, pk=None):
        user = request.user
        module_block_id = request.data.get('id')
        obj,created = ModuleBlockDone.objects.get_or_create(
           user=user,
           module_block_id=module_block_id
        )
        if not created:
           obj.delete()

        try:
            # Получаем урок и сразу считаем статистику
            from django.db.models import Count

            lesson_stats = ModuleBlock.objects.filter(
                id=module_block_id
            ).annotate(
                total_blocks=Count('module__lesson__modules__blocks'),
                done_blocks=Count(
                    'module__lesson__modules__blocks__moduleblockdone',
                    filter=Q(module__lesson__modules__blocks__moduleblockdone__user=user)
                )
            ).values('module__lesson', 'total_blocks', 'done_blocks').first()

            if lesson_stats:
                lesson_id = lesson_stats['module__lesson']
                total_blocks = lesson_stats['total_blocks']
                done_blocks = lesson_stats['done_blocks']

                print(total_blocks)
                print(done_blocks)

                # Обновляем статус урока
                if total_blocks > 0 and done_blocks == total_blocks:
                    LessonDone.objects.get_or_create(
                        user=user,
                        lesson_id=lesson_id
                    )
                else:
                    LessonDone.objects.filter(
                        user=user,
                        lesson_id=lesson_id
                    ).delete()

        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            print(f"Error updating lesson status: {e}")

        return Response(status=status.HTTP_200_OK)




class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class PhraseViewSet(viewsets.ModelViewSet):
    queryset = Phrase.objects.all()
    serializer_class = PhraseSerializer


class DictionaryGroupViewSet(viewsets.ModelViewSet):
    queryset = DictionaryGroup.objects.all()
    serializer_class = DictionaryGroupSerializer




class DictionaryItemViewSet(viewsets.ModelViewSet):
    queryset = DictionaryItem.objects.all()
    serializer_class = DictionaryItemSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        queryset = DictionaryItem.objects.all()

        if user.is_authenticated:
            favorites = DictionaryItemFavorite.objects.filter(
                user=user,
                dictionary_item=OuterRef("pk")
            )
            queryset = queryset.annotate(
                is_favorite=Exists(favorites)
            )
        else:
            queryset = queryset.annotate(
                is_favorite=models.Value(False, output_field=models.BooleanField())
            )

        return queryset

    @action(detail=True, methods=['post'], url_path='toggle_favorite')
    def toggle_favorite(self, request, id=None):
        user = request.user
        obj = self.get_object()
        obj, created = DictionaryItemFavorite.objects.get_or_create(
            user=user,
            dictionary_item=obj
        )
        if not created:
            obj.delete()
        return Response(status=status.HTTP_200_OK)
