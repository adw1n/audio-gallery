# Create your tasks here
from __future__ import absolute_import, unicode_literals
import os
import json
import decimal
import collections
import wave
import typing
import subprocess
import contextlib

from celery import shared_task
import matplotlib.figure
matplotlib.use("Agg")
import scipy.io.wavfile
import scipy.signal
import numpy
import matplotlib.pyplot
import matplotlib.cm
import pylab  # pylab import must be after the matplotlib.use call for the matplotlib.use("Agg") call to have an effect
from django.conf import settings
from celery.five import monotonic
from django.core.cache import cache
import celery.utils.log

from . import conf
from .models import AudioFile


logger = celery.utils.log.get_task_logger(__name__)


LOCK_EXPIRE = 60  # Lock expires in 1 minute
@contextlib.contextmanager
def memcache_lock(lock_id):
    """
    source code of this function has been taken from:
    http://docs.celeryproject.org/en/latest/tutorials/task-cookbook.html#ensuring-a-task-is-only-executed-one-at-a-time
    I removed the not needed oig.
    """
    logger.debug("in memcache_lock")
    timeout_at = monotonic() + LOCK_EXPIRE - 3
    status = cache.add(lock_id, "true", LOCK_EXPIRE)
    try:
        yield status
    finally:
        if monotonic() < timeout_at:
            cache.delete(lock_id)


def get_lock_id(pk: int) -> str:
    return "{0}-lock".format(pk)




def get_media_path(full_path: str) -> str:
    return os.path.relpath(full_path, settings.MEDIA_ROOT)


def round_half_up(num: float) -> int:
    return int(decimal.Decimal(num).quantize(0, decimal.ROUND_HALF_UP))


def get_wav_info(wav_file: str) -> typing.Tuple[numpy.ndarray, int]:
    wav = wave.open(wav_file, "r")
    frames = wav.readframes(-1)
    sound_info = numpy.fromstring(frames, "Int16")
    frame_rate = wav.getframerate()
    wav.close()
    return sound_info, frame_rate


@shared_task
def create_waveform(music_file_pk: int):
    logger.info("creating waveform")
    music_file = AudioFile.objects.get(pk=music_file_pk)
    waveform_path = os.path.join(music_file.waveform_upload_path, music_file._get_waveform_name())
    subprocess.call("waveform %s --waveformjs %s"
                    % (os.path.join(settings.MEDIA_URL, music_file.audio_file.path), waveform_path), shell=True)

    lock_id = get_lock_id(music_file.pk)
    with memcache_lock(lock_id) as acquired:
        if acquired:
            music_file.refresh_from_db()
            music_file.waveform.name = get_media_path(waveform_path)
            music_file.save()
        else:
            raise RuntimeError("Task could not acquire the lock.")
    logger.info("waveform created successfully")


@shared_task
def create_mp3(music_file_pk: int):
    logger.info("creating mp3")
    music_file = AudioFile.objects.get(pk=music_file_pk)
    mp3_path = os.path.join(settings.MEDIA_ROOT, music_file._get_mp3_name())
    subprocess.call("avconv -i %s -y %s" % (music_file.audio_file.path, mp3_path), shell=True)

    lock_id = get_lock_id(music_file.pk)
    with memcache_lock(lock_id) as acquired:
        if acquired:
            music_file.refresh_from_db()
            music_file.mp3.name = get_media_path(mp3_path)
            music_file.save()
        else:
            raise RuntimeError("Task could not acquire the lock.")
    logger.info("mp3 created successfully")


@shared_task
def create_spectrum(music_file_pk: int):
    logger.info("creating spectrum")
    music_file = AudioFile.objects.get(pk=music_file_pk)
    sampFreq, snd = scipy.io.wavfile.read(music_file.audio_file)
    snd = snd /pylab.np.iinfo(snd.dtype.type).max
    frequencies, Pxx = scipy.signal.welch(
        snd, sampFreq,scaling="spectrum",
        # for the nperseg I recommend using at least 1024
        nfft=conf.SPECTRUM_FFT_SIZE, nperseg=max(conf.SPECTRUM_FFT_SIZE, 1024))
    decibels = 10*pylab.log10(Pxx)
    spectrum_file = os.path.join(music_file.spectrum_upload_path, music_file._get_spectrum_name())
    with open(spectrum_file, "w") as outfile:
        json.dump(decibels.tolist(), outfile)

    lock_id = get_lock_id(music_file.pk)
    with memcache_lock(lock_id) as acquired:
        if acquired:
            music_file.refresh_from_db()
            music_file.spectrum.name = get_media_path(spectrum_file)
            music_file.save()
        else:
            raise RuntimeError("Task could not acquire the lock.")
    logger.info("spectrum created successfully")


FigureMargins = collections.namedtuple("FigureMargins", ["left_margin", "right_margin", "bottom_margin", "top_margin"])


def get_figure_margins(fig: matplotlib.figure.Figure) -> FigureMargins:
    # watch out for off-by-one errors
    left_margin = round_half_up(fig.subplotpars.left * conf.SPECTROGRAM_WIDTH)
    right_margin = conf.SPECTROGRAM_WIDTH - round_half_up(fig.subplotpars.right * conf.SPECTROGRAM_WIDTH)
    top_margin = round_half_up(conf.SPECTROGRAM_HEIGHT - fig.subplotpars.top * conf.SPECTROGRAM_HEIGHT)
    bottom_margin = round_half_up(conf.SPECTROGRAM_HEIGHT * fig.subplotpars.bottom)
    return FigureMargins(left_margin, right_margin, bottom_margin, top_margin)


# the value of this variable does not matter
# just keep it reasonable - between the values that exist for monitors
# (otherwise matplotlib might or might not be able to handle it)
# MY_DPI is used to guarantee that the generated image is of exactly the size in pixels we want
MY_DPI = 100  # type: int


@shared_task
def create_spectrogram(music_file_pk: int):
    logger.info("creating spectrogram")
    music_file = AudioFile.objects.get(pk=music_file_pk)
    sound_info, frame_rate = get_wav_info(music_file.audio_file)
    length_in_seconds = len(sound_info)/frame_rate

    fig = pylab.figure(figsize=(conf.SPECTROGRAM_WIDTH/MY_DPI, conf.SPECTROGRAM_HEIGHT/MY_DPI), dpi=MY_DPI)
    # matplotlib 1.4 default colormap was 'jet', matplotlib 2.0 changed it to 'viridis'
    # I've had much better results with 'jet' (nicer looking specgrams - more like audacity's specgrams)
    Pxx, freqs, bins, im = pylab.specgram(sound_info, Fs=frame_rate, scale_by_freq=False,
                                          cmap=matplotlib.cm.get_cmap("jet"))
    axes = pylab.gca()  # http://stackoverflow.com/questions/3777861/setting-y-axis-limit-in-matplotlib
    axes.set_xlim([0, length_in_seconds])
    axes.set_ylim([0, freqs[-1]])
    # TODO change yticks depending on max freq - frame_rate
    matplotlib.pyplot.yticks(list(range(0, 44000//2, 5000)))
    pylab.tight_layout()  # http://matplotlib.org/1.4.3/users/tight_layout_guide.html
    spectrogram_path = os.path.join(music_file.spectrogram_upload_path, music_file._get_spectrogram_name())
    pylab.savefig(spectrogram_path, transparent=True, dpi=MY_DPI)
    figure_margins = get_figure_margins(fig)

    lock_id = get_lock_id(music_file.pk)
    with memcache_lock(lock_id) as acquired:
        if acquired:
            music_file.refresh_from_db()
            music_file.spectrogram.name = get_media_path(spectrogram_path)
            music_file.TOP_IMG_MARGIN = figure_margins.top_margin
            music_file.BOTTOM_IMG_MARGIN = figure_margins.bottom_margin
            music_file.LEFT_IMG_MARGIN = figure_margins.left_margin
            music_file.RIGHT_IMG_MARGIN = figure_margins.right_margin
            music_file.save()
        else:
            raise RuntimeError("Task could not acquire the lock.")
    logger.info("spectrogram created successfully")
