from django.conf.urls import url
from .views import AudioFileDetail, AudioPageListView, SetLanguage


urlpatterns = [
    url(r'^$', AudioPageListView.as_view(), name='audio_pages'),
    url(r'^audio_file/(?P<pk>\w+)$', AudioFileDetail.as_view(), name='audio_file_detail'),
    url(r'^language$', SetLanguage.as_view(), name='set_language')
]
