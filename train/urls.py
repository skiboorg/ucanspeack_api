from django.urls import path
from .views import (
    CourseListView,
    LevelListByCourseView,
    TopicListByLevelView,
    TopicDetailView,
ToggleFavoriteAPIView,
FavoriteListAPIView
)

urlpatterns = [
    path("courses/", CourseListView.as_view(), name="courses"),

    path(
        "courses/<slug:course_slug>/levels/",
        LevelListByCourseView.as_view(),
        name="levels-by-course",
    ),

    path(
        "levels/<slug:level_slug>/topics/",
        TopicListByLevelView.as_view(),
        name="topics-by-level",
    ),

    path(
        "topics/<slug:slug>/",
        TopicDetailView.as_view(),
        name="topic-detail",
    ),
    path(
        "toggle_favorite/",
        ToggleFavoriteAPIView.as_view(),
        name="toggle-favorite",
    ),
    path('favorites/',
         FavoriteListAPIView.as_view()
         ),
]
