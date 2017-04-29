import os
import logging

from django.db import models
from django.conf import settings


logger = logging.getLogger(__name__)


class AudioFile(models.Model):
    title = models.CharField(max_length=100, unique=True)
    audio_file = models.FileField(upload_to='files/songs/%Y/%m/%d')

    waveform = models.FileField(upload_to='files/waveforms', blank=True, null=True, editable=False)
    mp3 = models.FileField(upload_to='files/songs/%Y/%m/%d', blank=True, null=True, editable=False)
    spectrogram = models.FileField(upload_to='files/spectrograms', blank=True, null=True, editable=False)
    spectrum = models.FileField(upload_to='files/spectrums', blank=True, null=True, editable=False)

    category = models.ForeignKey("Category", null=True)
    audio_page = models.ForeignKey("AudioPage", null=True)
    start_page = models.BooleanField(blank=True, default=False)  # TODO unique=True (only for true)

    # depending on the audio frequency matplotlib will generate different figures, with different margins
    TOP_IMG_MARGIN = models.IntegerField(blank=True, null=True, editable=False)
    BOTTOM_IMG_MARGIN = models.IntegerField(blank=True, null=True, editable=False)
    RIGHT_IMG_MARGIN = models.IntegerField(blank=True, null=True, editable=False)
    LEFT_IMG_MARGIN = models.IntegerField(blank=True, null=True, editable=False)

    def __str__(self):
        return self.title

    # TODO move those settings (*_upload_path) to settings.py
    # like this (settings.py): WAVEFORM_UPLOAD_PATH=os.path.join(settings.MEDIA_ROOT, "waveforms")
    @property
    def waveform_upload_path(self):
        return os.path.join(settings.MEDIA_ROOT, "waveforms")
    @property
    def spectrogram_upload_path(self):
        return os.path.join(settings.MEDIA_ROOT, "spectrograms")
    @property
    def spectrum_upload_path(self):
        return os.path.join(settings.MEDIA_ROOT, "spectrum")
    @property
    def audio_file_name(self)->str:
        '''
        file base name without extension
        '''
        return os.path.splitext(os.path.basename(self.audio_file.path))[0]

    def _get_spectrum_name(self):
        return self.audio_file_name + "_spectrum.json"
    def _get_waveform_name(self):
        return self.audio_file_name + "_waveform.json"
    def _get_spectrogram_name(self):
        return self.audio_file_name + "_spectrogram.png"
    def _get_mp3_name(self)->str:
        return os.path.splitext(self.audio_file.name)[0] + ".mp3"

    @property
    def spectrogram_url(self):
        if self.spectrogram:
            return self.spectrogram.url
    @property
    def spectrum_url(self):
        if self.spectrum:
            return self.spectrum.url
    @property
    def mp3_url(self):
        if self.mp3:
            return self.mp3.url
    @property
    def waveform_url(self):
        if self.waveform:
            return self.waveform.url

    def clean_old_file(self):
        # TODO finish this
        pass

    def create_files(self):
        from .tasks import create_waveform, create_mp3, create_spectrogram, create_spectrum
        create_spectrogram.delay(self.pk)
        create_waveform.delay(self.pk)
        create_spectrum.delay(self.pk)
        create_mp3.delay(self.pk)

    def save(self, *args, **kwargs):
        file_changed = False
        if self.pk:
            old = AudioFile.objects.get(pk=self.pk)
            if self.audio_file != old.audio_file:
                logger.info("audio file has changed")
                file_changed = True
        else:
            file_changed = True
        super().save(*args, **kwargs)
        if file_changed:
            # TODO self.clean_old_file()
            self.create_files()


class AudioPage(models.Model):
    name = models.CharField(max_length=100)
    categories = models.ManyToManyField("Category", blank=True)
    photo = models.ImageField(upload_to='files/photos/%Y/%m/%d', null=True, blank=True)
    description = models.TextField(blank=True)
    page_number = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent_category = models.ForeignKey("self", null=True, blank=True)

    def __str__(self):
        if self.parent_category:
            return str(self.parent_category) + "->%s" % self.name
        else:
            return self.name

    class Meta:
        verbose_name_plural = "Categories"
