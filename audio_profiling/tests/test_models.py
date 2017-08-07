import unittest.mock

from django.test import TransactionTestCase
from django.db import transaction

from .. import models


class AudioFileTests(TransactionTestCase):
    def setUp(self):
        models.AudioFile.create_files = unittest.mock.MagicMock()
        self.music_file = models.AudioFile.objects.create(title="test_file", audio_file="sample.wav")

    def test_create_files_is_called_on_object_creation(self):
        self.assertEqual(models.AudioFile.create_files.call_count, 1)

    def test_create_files_not_fired_when_nothing_changes(self):
        models.AudioFile.create_files.reset_mock()
        self.music_file.create_files = unittest.mock.MagicMock()
        with transaction.atomic():
            self.music_file.save()
        self.music_file.create_files.assert_not_called()

    def test_create_files_not_called_until_transaction_is_over(self):
        models.AudioFile.create_files.reset_mock()
        self.music_file.audio_file.name = "new/path/to/file.wav"
        with transaction.atomic():
            self.music_file.save()
            self.music_file.create_files.assert_not_called()

    def test_create_files_called_when_audio_file_changes(self):
        models.AudioFile.create_files.reset_mock()
        self.music_file.audio_file.name = "new/path/to/file.wav"
        with transaction.atomic():
            self.music_file.save()
        self.assertEqual(self.music_file.create_files.call_count, 1)
