import unittest.mock

from django.test import TestCase

from .. import models


class AudioFileTests(TestCase):
    def setUp(self):
        models.AudioFile.create_files = unittest.mock.MagicMock()
        self.music_file = models.AudioFile.objects.create(title="test_file", audio_file="sample.wav")

    def test_create_files_is_called_on_object_creation(self):
        self.assertEqual(models.AudioFile.create_files.call_count, 1)

    def test_create_files_not_fired_when_nothing_changes(self):
        self.music_file.create_files = unittest.mock.MagicMock()
        self.music_file.save()
        self.music_file.create_files.assert_not_called()

    def test_create_files_called_when_audio_file_changes(self):
        self.music_file.create_files = unittest.mock.MagicMock()
        self.music_file.audio_file.name = "new/path/to/file.wav"
        self.music_file.save()
        self.assertEqual(self.music_file.create_files.call_count, 1)
