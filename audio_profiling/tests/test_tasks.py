import os
import unittest.mock
import typing
import math
import operator
from contextlib import contextmanager

import numpy
import pylab
from django.test import TestCase
from django.conf import settings

from ..models import AudioFile
from .. import tasks
from .. import conf


@contextmanager
def mock_generator(_):
    yield True
tasks.memcache_lock = mock_generator


def generate_audio() -> numpy.array:
    dtype = numpy.dtype("int16")
    MAX_INT = pylab.np.iinfo(dtype.type).max

    def silence(sample_rate: int =44100, duration_ms: int = 500) -> typing.List[int]:
        return [0]*int(duration_ms * (sample_rate / 1000.0))

    def sinewave(freq, sample_rate: int =44100, duration_ms: int = 500, volume: float = 1) -> typing.List[int]:
        number_of_samples = duration_ms * (sample_rate / 1000.0)
        return [volume * math.sin(2 * math.pi * freq * (x / sample_rate))*MAX_INT for x in range(int(number_of_samples))]

    return numpy.array(sinewave(4000, volume=0.25) + silence() + sinewave(8000, volume=0.5) + silence()
                       + sinewave(12000,volume=0.75), dtype=dtype)


class AudioFileTasksTests(TestCase):
    def setUp(self):
        self.music_file = AudioFile.objects.create(title="some title")  # type: AudioFile
        self.wav_song_name = "sample_music.wav"  # type: str
        self.wav_song_path = os.path.join(settings.MEDIA_ROOT, "files/songs/2017/01/02", self.wav_song_name)  # type: str
        self.music_file.audio_file.name = self.wav_song_path
        self.music_file.save()
        AudioFile.create_files = unittest.mock.MagicMock()

    def test_get_media_path(self):
        expected = "files/songs/2017/01/02/sample_music.mp3"
        full_path = os.path.join(settings.MEDIA_ROOT, expected)
        self.assertEqual(tasks.get_media_path(full_path), expected)

    def test_round_half_up(self):
        for i in range(5):
            self.assertEqual(tasks.round_half_up(i+0.5), i+1)
            self.assertEqual(tasks.round_half_up(i+0.49), i)

    def test_get_figure_margins(self):
        conf.SPECTROGRAM_WIDTH = 1900
        conf.SPECTROGRAM_HEIGHT = 500
        fig = unittest.mock.Mock()
        fig.subplotpars = unittest.mock.Mock(left=0.0361038011696, right=0.990263157895, bottom=0.0774444444444,
                                           top=0.963)
        figure_margins = tasks.get_figure_margins(fig)
        expected_margins = tasks.FigureMargins(left_margin=69, right_margin=18, bottom_margin=39, top_margin=19)
        self.assertEqual(figure_margins, expected_margins)

    @unittest.mock.patch('subprocess.call')
    def test_create_mp3(self, subprocess_call_mock: unittest.mock.MagicMock):
        mp3_song_path = self.wav_song_path.replace("wav", "mp3")  # type: str
        tasks.create_mp3(self.music_file.pk)
        self.music_file.refresh_from_db()
        self.assertEqual(self.music_file.mp3.name, tasks.get_media_path(mp3_song_path))
        subprocess_call_mock.assert_called_with("avconv -i %s -y %s" % (self.music_file.audio_file.path, mp3_song_path),
                                                shell=True)

    @unittest.mock.patch('subprocess.call')
    def test_create_waveform(self, subprocess_call_mock: unittest.mock.MagicMock):
        waveform_path = os.path.join(self.music_file.waveform_upload_path, self.music_file._get_waveform_name())
        tasks.create_waveform(self.music_file.pk)
        self.music_file.refresh_from_db()
        self.assertEqual(self.music_file.waveform.name, tasks.get_media_path(waveform_path))
        subprocess_call_mock.assert_called_with(
            "waveform %s --waveformjs %s" % (os.path.join(settings.MEDIA_URL, self.music_file.audio_file.path),
                                             waveform_path),
            shell=True)

    @unittest.mock.patch('json.dump')
    @unittest.mock.patch('scipy.io.wavfile.read')
    def test_create_spectrum(self, scipy_io_wavfile_read_mock: unittest.mock.MagicMock,
                             json_dump_mock: unittest.mock.MagicMock):
        sample_audio = generate_audio()
        sample_freq = 44100  # type: int
        scipy_io_wavfile_read_mock.return_value = (sample_freq, sample_audio)
        tasks.create_spectrum(self.music_file.pk)
        self.assertEqual(scipy_io_wavfile_read_mock.call_count, 1)
        self.assertEqual(json_dump_mock.call_count, 1)
        self.music_file.refresh_from_db()
        spectrum_path = os.path.join(self.music_file.spectrum_upload_path, self.music_file._get_spectrum_name())
        self.assertEqual(os.path.normpath(self.music_file.spectrum.path), os.path.normpath(spectrum_path))

        self.assertEqual(len(json_dump_mock.call_args), 2)
        self.assertEqual(len(json_dump_mock.call_args[0]), 2)
        decibels = json_dump_mock.call_args[0][0]  # type: typing.List[int]
        self.assertEqual(len(decibels), conf.SPECTRUM_FFT_SIZE/2+1)
        ranges = [int(len(decibels)/(sample_freq/2)*7000), int(len(decibels)/(sample_freq/2)*11000)]
        max_index_4k_sine, max_value_4k_sine = max(enumerate(decibels[:ranges[0]]), key=operator.itemgetter(1))
        max_index_8k_sine, max_value_8k_sine = max(enumerate(decibels[ranges[0]:ranges[1]]), key=operator.itemgetter(1))
        max_index_12k_sine, max_value_12k_sine = max(enumerate(decibels[ranges[1]:]), key=operator.itemgetter(1))
        max_index_8k_sine += ranges[0]
        max_index_12k_sine += ranges[1]
        self.assertTrue(max_index_4k_sine < max_index_8k_sine < max_index_12k_sine)
        self.assertTrue(max_value_12k_sine > max_value_8k_sine > max_value_4k_sine)

    @unittest.mock.patch('pylab.savefig')
    @unittest.mock.patch('audio_profiling.tasks.get_wav_info')
    def test_create_spectrogram(self, get_wav_info_mock: unittest.mock.MagicMock,
                                pylab_savefig_mock: unittest.mock.MagicMock):
        get_wav_info_mock.return_value = (generate_audio(), 44100)
        tasks.create_spectrogram(self.music_file.pk)
        self.music_file.refresh_from_db()
        spectrogram_path = os.path.join(self.music_file.spectrogram_upload_path, self.music_file._get_spectrogram_name())
        self.assertEqual(os.path.normpath(self.music_file.spectrogram.path), os.path.normpath(spectrogram_path))
        self.assertTrue(self.music_file.TOP_IMG_MARGIN)
        self.assertTrue(self.music_file.BOTTOM_IMG_MARGIN)
        self.assertTrue(self.music_file.LEFT_IMG_MARGIN)
        self.assertTrue(self.music_file.RIGHT_IMG_MARGIN)
        self.assertEqual(pylab_savefig_mock.call_count, 1)
