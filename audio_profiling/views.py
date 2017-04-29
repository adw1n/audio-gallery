import logging
import typing
from collections import namedtuple

from django.shortcuts import redirect
import django
import django.utils.translation
from django.views.generic import View, ListView, DetailView
import modeltranslation

from . import models
from .models import AudioFile, AudioPage
from . import conf

logger = logging.getLogger(__name__)


class SetLanguage(View):
    """
    TODO I should have used:
     https://docs.djangoproject.com/en/1.10/topics/i18n/translation/#django.views.i18n.set_language
    instead of rolling my own SetLanguage view...
    """
    # TODO https://docs.djangoproject.com/en/1.8/topics/i18n/translation/#the-set-language-redirect-view
    def get(self, request):
        user_language = request.GET.get("language", "en")  # type: str
        django.utils.translation.activate(user_language)
        request.session[django.utils.translation.LANGUAGE_SESSION_KEY] = user_language
        referer = request.META.get("HTTP_REFERER")
        if referer and "audio_file" in referer:  # TODO remove hardcoded URL...
            return redirect(referer)
        return redirect(request.GET.get("link", "/"))


AudioPageCategories = namedtuple("AudioPageCategories", ["audio_page", "categories"])
CategoryAudioFileTuple = namedtuple("CategoryAudioFileTuple", ["category", "audio_file"])
CategorySubcategoriesTuple = namedtuple("CategorySubcategoriesTuple", ["category", "subcategories"])
class AudioListMixin:
    @staticmethod
    def sort_by_page_number(instruments: modeltranslation.manager.MultilingualQuerySet) -> typing.List[models.AudioPage]:
        return sorted(instruments, key=lambda obj:  obj.page_number if obj.page_number is not None else float("inf"))

    def get_context_data(self, context)->typing.Dict:
        # normally we would write AudioPage.objects.all().order_by((0 * django.db.models.F('page_number')).desc(), 'name')
        # but django-modeltranslation has a bug, long story short we cannot do order_by with any expression
        # there is a pending pull request:
        # https://github.com/deschler/django-modeltranslation/pull/398
        # until that gets merged, we will use the slower approach of using sort_by_page_number function
        audio_pages = AudioPage.objects.all().order_by("name")
        audio_pages = AudioListMixin.sort_by_page_number(audio_pages)

        audio_pages_categories = []  # type: typing.List[AudioPageCategories]
        for audio_page in audio_pages:
            categories = []  # type: typing.List[typing.Union[CategoryAudioFileTuple,CategorySubcategoriesTuple]]
            for category in audio_page.categories.all():
                if not category.parent_category and AudioFile.objects.filter(audio_page=audio_page,
                                                                             category=category).count():
                    categories.append(
                        CategoryAudioFileTuple(category,
                                               AudioFile.objects.filter(audio_page=audio_page,
                                                                        category=category).first()
                                               ))
                else:
                    subcategories = []  # type: typing.List[CategoryAudioFileTuple]
                    for subcategory in category.category_set.all():
                        if AudioFile.objects.filter(audio_page=audio_page, category=subcategory).count():
                            subcategories.append(
                                CategoryAudioFileTuple(subcategory,
                                                       AudioFile.objects.filter(audio_page=audio_page,
                                                                                category=subcategory).first()
                                                       ))
                    if subcategories:
                        categories.append((CategorySubcategoriesTuple(category, subcategories)))
            audio_pages_categories.append(AudioPageCategories(audio_page, categories))

        context["audio_pages_categories"] = audio_pages_categories
        return context


class AudioFileDetail(DetailView, AudioListMixin):
    model = AudioFile
    template_name = "audio_profiling/audiofile_detail.html"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        AudioListMixin.get_context_data(self, context)
        context["SPECTRUM_FFT_SIZE"] = conf.SPECTRUM_FFT_SIZE
        context["SPECTROGRAM_WIDTH"] = conf.SPECTROGRAM_WIDTH
        context["SPECTROGRAM_HEIGHT"] = conf.SPECTROGRAM_HEIGHT
        return context


class AudioPageListView(ListView, AudioListMixin):
    model = AudioPage
    context_object_name = "audio_pages"
    template_name = "audio_profiling/base.html"

    def get_context_data(self, **kwargs):
        context = super(AudioPageListView, self).get_context_data(**kwargs)
        return AudioListMixin.get_context_data(self, context)

    def get(self, request, *args, **kwargs):
        start_page_music = AudioFile.objects.filter(start_page=True).first()
        if start_page_music:
            return redirect("audio_profiling:audio_file_detail", pk=start_page_music.pk)
        return super(AudioPageListView, self).get(request, *args, **kwargs)
