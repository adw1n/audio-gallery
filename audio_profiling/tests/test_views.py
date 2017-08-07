import unittest.mock

import typing
import django.test
import django.views.generic
from django.core.urlresolvers import reverse

from .. import models
from .. import views


# mypy can't handle static function variables (or I don't know how to set it up to work)
@typing.no_type_check
def get_dummy_audio_file(category: models.Category, instrument: models.AudioPage) -> models.AudioFile:
    get_dummy_audio_file.counter += 1
    return models.AudioFile.objects.create(
        title="song %s" % get_dummy_audio_file.counter,
        audio_file="dummy_file_%s.wav" % get_dummy_audio_file.counter,
        waveform="dummy_waveform_%s.json" % get_dummy_audio_file.counter,
        mp3="dummy_mp3_%s.mp3" % get_dummy_audio_file.counter,
        spectrogram="dummy_spectrogram_%s" % get_dummy_audio_file.counter,
        spectrum="dummy_spectrum_%s" % get_dummy_audio_file.counter,
        category=category,
        audio_page=instrument
    )
get_dummy_audio_file.counter = 0


class ViewTestCase(django.test.TestCase):
    def setUp(self):
        models.AudioFile.create_files = unittest.mock.MagicMock()
        self.mario = models.AudioPage.objects.create(name_en="Super Mario Bros", name_pl="Mario",
                                                     description_en="video game created by Nintendo")
        self.guild_wars = models.AudioPage.objects.create(
            name_en="Guild Wars", name_pl="Wojny Gildii", description_en="MMORPG",
            description_pl="MMORPG stworzone przez ArenaNet")
        self.machinarium = models.AudioPage.objects.create(
            name_en="Machinarium", name_pl="Machinarium", description_en="Indie game",
            description_pl="Niezależna gra komputerowa.", page_number=1)
        self.lvls = [models.Category.objects.create(name_en="level one", name_pl="poziom pierwszy"),
                     models.Category.objects.create(name_en="level two", name_pl="poziom drugi"),
                     models.Category.objects.create(name_en="level three", name_pl="poziom trzeci")]
        third_lvl = self.lvls[-1]
        self.lvls.append(models.Category.objects.create(name_en="submarine theme", name_pl="motyw łodzi podwodnej",
                                                        parent_category=third_lvl))
        self.lvls.append(
            models.Category.objects.create(name_en="fire theme", name_pl="motyw smoka", parent_category=third_lvl))
        self.mario.categories.add(*self.lvls)
        self.lvls_files = [None]*len(self.lvls)
        for index, level in enumerate(self.lvls):
            if level != third_lvl:
                self.lvls_files[index] = get_dummy_audio_file(level, self.mario)

        self.ugroz_theme = models.Category.objects.create(name_en="Ugroz theme")
        self.fow_theme = models.Category.objects.create(name_en="FOW theme")
        self.guild_wars.categories.add(self.ugroz_theme)
        self.guild_wars_ugroz_theme_file=get_dummy_audio_file(self.ugroz_theme, self.guild_wars)

        self.basement_theme = models.Category.objects.create(name_en="basement theme")
        self.machinarium.categories.add(self.basement_theme)
        self.machinarium_basement_theme_audio_file = get_dummy_audio_file(self.basement_theme, self.machinarium)


class AudioListMixinTests(ViewTestCase):
    def test_get_context_data(self):
        factory = django.test.RequestFactory()
        url = reverse("audio_profiling:audio_file_detail", kwargs={"pk": self.machinarium_basement_theme_audio_file.pk})
        request = factory.get(url)
        view = views.AudioFileDetail()
        view.request = request
        view.object = self.machinarium_basement_theme_audio_file

        context = django.views.generic.DeleteView.get_context_data(
            view, **{"object": self.machinarium_basement_theme_audio_file})
        context = views.AudioListMixin.get_context_data(view, context)
        expected_audio_pages_categories = [
            views.AudioPageCategories(
                audio_page=self.machinarium,
                categories=[views.CategoryAudioFileTuple(self.basement_theme, self.machinarium_basement_theme_audio_file)]
            ),
            views.AudioPageCategories(
                audio_page=self.guild_wars,
                categories=[views.CategoryAudioFileTuple(self.ugroz_theme, self.guild_wars_ugroz_theme_file)]
            ),
            views.AudioPageCategories(
                audio_page=self.mario,
                categories=sorted([
                    views.CategoryAudioFileTuple(self.lvls[i], self.lvls_files[i]) for i in range(2)
                ] + [
                    views.CategorySubcategoriesTuple(
                       self.lvls[2],
                       sorted(
                           [views.CategoryAudioFileTuple(self.lvls[i], self.lvls_files[i]) for i in range(3, len(self.lvls))],
                           key=lambda x: x.category.name)
                    )
                ], key=lambda x: x.category.name)
            )
        ]
        self.assertEqual(context["audio_pages_categories"], expected_audio_pages_categories)


class AudioFileDetailTests(ViewTestCase):
    def test_get_audio_file(self):
        url = reverse("audio_profiling:audio_file_detail", kwargs={"pk": self.machinarium_basement_theme_audio_file.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "audio_profiling/audiofile_detail.html")
        self.assertContains(response, self.machinarium.name_en)
        self.assertContains(response, self.machinarium.description_en)
        self.assertContains(response, self.machinarium_basement_theme_audio_file.audio_file.url)
        self.assertContains(response, self.machinarium_basement_theme_audio_file.spectrogram.url)
        self.assertContains(response, self.machinarium_basement_theme_audio_file.mp3.url)
        self.assertContains(response, self.machinarium_basement_theme_audio_file.spectrum.url)

    def test_file_with_missing_one_link_renders_correctly(self):
        self.machinarium_basement_theme_audio_file.spectrogram = None
        self.machinarium_basement_theme_audio_file.save()
        url = reverse("audio_profiling:audio_file_detail",
                      kwargs={"pk": self.machinarium_basement_theme_audio_file.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "audio_profiling/audiofile_detail.html")
        self.assertContains(response, self.machinarium.name_en)
        self.assertContains(response, self.machinarium.description_en)
        self.assertContains(response, self.machinarium_basement_theme_audio_file.audio_file.url)
        self.assertContains(response, self.machinarium_basement_theme_audio_file.mp3.url)
        self.assertContains(response, self.machinarium_basement_theme_audio_file.spectrum.url)

    def test_file_with_missing_all_links_renders_correctly(self):
        self.machinarium_basement_theme_audio_file.spectrogram = None
        self.machinarium_basement_theme_audio_file.waveform = None
        self.machinarium_basement_theme_audio_file.mp3 = None
        self.machinarium_basement_theme_audio_file.spectrum = None
        self.machinarium_basement_theme_audio_file.save()
        url = reverse("audio_profiling:audio_file_detail",
                      kwargs={"pk": self.machinarium_basement_theme_audio_file.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "audio_profiling/audiofile_detail.html")
        self.assertContains(response, self.machinarium.name_en)
        self.assertContains(response, self.machinarium.description_en)


class AudioPageListViewTests(ViewTestCase):
    def test_all_categories_are_presented_to_the_user(self):
        url = reverse("audio_profiling:audio_pages")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "audio_profiling/base.html")
        self.assertContains(response, self.mario.name_en)
        self.assertContains(response, self.guild_wars.name_en)
        self.assertContains(response, self.machinarium.name_en)
        for level in self.lvls:
            self.assertContains(response, level.name_en)
        self.assertContains(response, self.ugroz_theme.name_en)

        # no AudioFile associated with this category, hence it shouldn't get rendered
        self.assertNotContains(response, self.fow_theme.name_en)
        self.assertContains(response, self.basement_theme.name_en)
        response_body = response.content.decode("utf-8")
        self.assertTrue(response_body.find(self.machinarium.name_en)
                        < response_body.find(self.guild_wars.name_en)
                        < response_body.find(self.mario.name_en))

    def test_redirect_when_start_page_is_set(self):
        self.machinarium_basement_theme_audio_file.start_page = True
        self.machinarium_basement_theme_audio_file.save()
        url = reverse("audio_profiling:audio_pages")
        expected_url = reverse("audio_profiling:audio_file_detail",
                               kwargs={"pk": self.machinarium_basement_theme_audio_file.pk})
        response = self.client.get(url)
        self.assertRedirects(response, expected_url)


class SetLanguageTests(django.test.TestCase):
    pass
