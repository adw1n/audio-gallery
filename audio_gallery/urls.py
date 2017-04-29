from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    url(r"^admin/", include(admin.site.urls)),
    url(r"^", include("audio_profiling.urls", namespace="audio_profiling", app_name="audio_profiling")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
