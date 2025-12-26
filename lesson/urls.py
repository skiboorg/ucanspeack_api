from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import path,include


router = DefaultRouter()
router.register("courses", CourseViewSet)
router.register("levels", LevelViewSet)
router.register("lessons", LessonViewSet)
router.register("modules", ModuleViewSet)
router.register("videos", VideoViewSet)
router.register("phrases", PhraseViewSet)
router.register("dictionary-groups", DictionaryGroupViewSet)
router.register("dictionary-items", DictionaryItemViewSet)



urlpatterns = [
    path('dictionary_favorites/', DictionaryItemFavoriteListAPIView.as_view()),
    path('lesson_item_favorites/', LessonItemFavoriteListAPIView.as_view()),
] + router.urls