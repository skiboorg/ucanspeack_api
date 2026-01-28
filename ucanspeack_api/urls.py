from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

from user.views import CustomTokenCreateView
from user.logout import CustomLogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),

    # path('api/store/', include('store.urls')),
    path('api/lesson/', include('lesson.urls')),
    path('api/trainer/', include('train.urls')),
    path('api/user/', include('user.urls')),
    path("api/search/", include("search.urls")),
    path('auth/', include('djoser.urls')),
    #path('auth/', include('djoser.urls.authtoken')),
    path("auth/token/login/", CustomTokenCreateView.as_view(), name="login"),
    path('auth/token/logout/', CustomLogoutView.as_view(), name='custom-logout'),
    path("ckeditor5/", include('django_ckeditor_5.urls'), name="ck_editor_5_upload_file"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)