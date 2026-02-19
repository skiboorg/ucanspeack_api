from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter
from user.services.school import SchoolPupilViewSet

router = DefaultRouter()
router.register(r'school-pupils', SchoolPupilViewSet, basename='school-pupils')

urlpatterns = [
    path('me', views.GetUser.as_view()),
    path('update', views.UpdateUser.as_view()),

]+ router.urls
