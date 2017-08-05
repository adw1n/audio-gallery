import time
import os
import typing
import shutil

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
import numpy
import scipy.io.wavfile
from pyvirtualdisplay import Display

from audio_gallery import settings
from audio_profiling import models, conf, tasks
from django.test.utils import override_settings
from audio_profiling.tests import audio_helpers


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_TEST_MEDIA_ROOT = os.path.join(SCRIPT_DIR, "test_media")


def generate_wav_files(dir_to_save_in: str) -> typing.List[str]:
    """
    generating open-source music...
    """
    files = ["a.wav", "b.wav", "c.wav"]
    files = [os.path.join(dir_to_save_in, file_name) for file_name in files]
    a_data=numpy.array(
        audio_helpers.sinewave(4000, volume=0.25, duration_ms=10000) +
        audio_helpers.silence(duration_ms=5000) +
        audio_helpers.sinewave(8000, volume=0.5, duration_ms=10000) +
        audio_helpers.silence(duration_ms=5000) +
        audio_helpers.sinewave(12000, volume=0.75, duration_ms=10000),
        dtype=audio_helpers.DTYPE)
    scipy.io.wavfile.write(files[0], 44100, a_data)

    b_data = numpy.array(
        audio_helpers.sinewave(12000, volume=0.25, duration_ms=10000) +
        audio_helpers.silence(duration_ms=5000) +
        audio_helpers.sinewave(8000, volume=0.5, duration_ms=10000) +
        audio_helpers.silence(duration_ms=5000) +
        audio_helpers.sinewave(4000, volume=0.75, duration_ms=10000),
        dtype=audio_helpers.DTYPE)
    scipy.io.wavfile.write(files[1], 44100, b_data)

    c_data = numpy.array(
        audio_helpers.sinewave(10000, volume=0.25, duration_ms=10000) +
        audio_helpers.silence(duration_ms=5000) +
        audio_helpers.sinewave(8000, volume=0.75, duration_ms=10000) +
        audio_helpers.silence(duration_ms=5000) +
        audio_helpers.sinewave(6000, volume=0.5, duration_ms=10000) +
        audio_helpers.silence(duration_ms=5000) +
        audio_helpers.sinewave(4000, volume=0.75, duration_ms=10000),
        dtype=audio_helpers.DTYPE)
    scipy.io.wavfile.write(files[2], 44100, c_data)

    return [tasks.get_media_path(file) for file in files]


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@override_settings(MEDIA_ROOT=_TEST_MEDIA_ROOT)
class FunctionalTest(StaticLiveServerTestCase):
    AUDIO_FILES_DIR = os.path.join(_TEST_MEDIA_ROOT, "files/songs/2017/01/02")

    @classmethod
    def _create_dummy_media_dir(cls):
        os.makedirs(_TEST_MEDIA_ROOT)
        os.makedirs(cls.AUDIO_FILES_DIR)
        os.makedirs(os.path.join(_TEST_MEDIA_ROOT, "waveforms"))
        os.makedirs(os.path.join(_TEST_MEDIA_ROOT, "spectrum"))
        os.makedirs(os.path.join(_TEST_MEDIA_ROOT, "spectrograms"))

    @classmethod
    def _clean_dummy_media_dir(cls):
        shutil.rmtree(_TEST_MEDIA_ROOT)

    def setUp(self):
        self.display = Display(visible=0, size=(800, 600))
        self.display.start()
        self.browser = webdriver.Chrome()
        self._create_dummy_media_dir()
        self.files = generate_wav_files(self.AUDIO_FILES_DIR)
        super().setUp()

    def tearDown(self):
        self.browser.quit()
        self.display.stop()
        self._clean_dummy_media_dir()
        super().tearDown()

    def is_audio_paused(self):
        return self.browser.execute_script('return $("audio")[0].paused')

    def pause_audio(self) -> None:
        self.browser.execute_script('$("audio")[0].pause()')
        time.sleep(0.5)
        self.assertTrue(self.is_audio_paused())

    def play_audio(self):
        self.browser.execute_script('$("audio")[0].play()')
        time.sleep(0.5)
        self.assertFalse(self.is_audio_paused())

    def check_timestamp_lines_in_sync(self, audio: models.AudioFile, audio_len: float):
        """
        Check whether progress markers have reasonable values.
        :param audio: audio beging played
        :param audio_len: length of the audio file in seconds
        """

        current_audio_time = self.get_current_audio_time()
        audio_progress = (current_audio_time/ audio_len)

        # check waveform
        wave = self.browser.execute_script('return $("wave:has(wave)")')
        wave_timestamp = self.browser.execute_script('return $("wave wave")')
        self.assertEqual(len(wave), 1)
        self.assertEqual(len(wave_timestamp), 1)
        wave = wave[0]
        wave_timestamp = wave_timestamp[0]
        self.assertGreaterEqual(wave.size['width'], 0)
        self.assertGreaterEqual(wave_timestamp.size['width'], 0)
        self.assertAlmostEqual(
            wave_timestamp.size['width'],
            wave.size['width'] * audio_progress,
            delta=max(1, audio_len * 0.01))


        # check spectrogram
        spectrogram_image = self.browser.find_element_by_id("spectogram")
        spectrogram_timestamp = self.browser.find_element_by_id("spectogramTimeStamp")

        current_img_scaling = self.get_current_image_scaling()
        spectrogram_image_width_without_margins = spectrogram_image.size["width"] -(audio.LEFT_IMG_MARGIN+audio.RIGHT_IMG_MARGIN) * current_img_scaling
        if spectrogram_timestamp.size['width']==0:
            spectrogram_timestamp_with_without_left_margin = 0
        else:
            spectrogram_timestamp_with_without_left_margin = spectrogram_timestamp.size['width'] - (audio.LEFT_IMG_MARGIN * current_img_scaling)

        self.assertGreaterEqual(spectrogram_timestamp_with_without_left_margin, 0)
        self.assertGreaterEqual(spectrogram_image_width_without_margins, 0)
        self.assertAlmostEqual(
            spectrogram_timestamp_with_without_left_margin,
            spectrogram_image_width_without_margins*audio_progress,
            delta=max(1, spectrogram_timestamp_with_without_left_margin*0.1))



        # compare spectrogram's timestamp with waveform's timestamp
        self.assertAlmostEqual(
            spectrogram_timestamp_with_without_left_margin,
            wave_timestamp.size['width'],
            delta=max(1, wave_timestamp.size['width'] * 0.1))

    def get_current_audio_time(self) -> float:
        return self.browser.execute_script('return $("audio")[0].currentTime')

    def get_current_image_scaling(self) -> float:
        """
        if image normally has 1000px width, but is displayed with 500px width then scaling == 50%
        """
        return self.browser.execute_script('return $("#spectogram").width()')/conf.SPECTROGRAM_WIDTH

    def set_audio_position(self, audio_time: float) -> None:
        self.browser.execute_script('$("audio")[0].currentTime=%s'%audio_time)
        time.sleep(0.1)

    def get_spectrum_data(self) -> str:
        return self.browser.execute_script('return $("#canvas")[0].toDataURL()')

    def check_internalization(self, audio_page: models.AudioPage, language: str):
        assert language in [language_code[0] for language_code in settings.LANGUAGES]

        self.assertIn(getattr(audio_page, "name_"+language), self.browser.page_source)
        self.assertIn(getattr(audio_page, "name_"+language), self.browser.page_source)

        assertEn = getattr(self, "assert" + ("" if language == "en" else "Not") + "In")
        assertEn("Instantaneous frequency spectrum of the sound (at the end-averaged)", self.browser.page_source)
        assertEn("Changes of sound amplitude in time", self.browser.page_source)
        assertEn("Aggregate image of frequency spectrum changes in time", self.browser.page_source)

        assertPl = getattr(self, "assert" + ("Not" if language == "en" else "") + "In")
        assertPl("Chwilowe spektrum częstotliwości dźwięku (na końcu - uśrednione)", self.browser.page_source)
        assertPl("Zmiany amplitudy dźwięku w czasie", self.browser.page_source)
        assertPl("Sumaryczny obraz zmian spektrum dźwięku w czasie", self.browser.page_source)

    def check_spectrogram_loaded(self, audio: models.AudioFile):
        self.assertTrue(
            self.browser.execute_script(
                'return $("#spectogram")[0].complete && $("#spectogram")[0].naturalWidth !== 0'
            )
        )
        spectrogram_source = self.browser.execute_script('return $("#spectogram")[0].src')
        self.assertEqual(spectrogram_source.split("/media/")[1], audio.spectrogram.name)

    def check_audio_loaded(self, audio: models.AudioFile):
        audio_sources = self.browser.execute_script('return $("audio source").toArray().map(source => source.src)')
        self.assertEqual(len(audio_sources), 2)
        self.assertEqual(audio_sources[0].split("/media/")[1], audio.audio_file.name)
        self.assertEqual(audio_sources[1].split("/media/")[1], audio.mp3.name)

    def check_page(self, audio_page: models.AudioPage, audio: models.AudioFile, language: str):
        AUDIO_LEN = self.browser.execute_script('return $("audio")[0].duration')
        self.assertGreater(AUDIO_LEN, 20)
        self.assertLess(AUDIO_LEN, 60)

        self.check_audio_loaded(audio)
        self.check_internalization(audio_page, language)
        self.check_spectrogram_loaded(audio)

        SPECTRUM_AT_THE_BEGINNING = self.get_spectrum_data()
        self.check_timestamp_lines_in_sync(audio, AUDIO_LEN)
        self.play_audio()
        # let the audio play
        time.sleep(5)
        self.pause_audio()
        self.check_timestamp_lines_in_sync(audio, AUDIO_LEN)
        self.assertNotEqual(SPECTRUM_AT_THE_BEGINNING, self.get_spectrum_data())

        # user only wants to listen to the end of the audio
        self.set_audio_position(20)
        self.check_timestamp_lines_in_sync(audio, AUDIO_LEN)

        # user wants to start listening from the beginning
        self.set_audio_position(0)
        self.check_timestamp_lines_in_sync(audio, AUDIO_LEN)
        self.assertEqual(SPECTRUM_AT_THE_BEGINNING, self.get_spectrum_data())
