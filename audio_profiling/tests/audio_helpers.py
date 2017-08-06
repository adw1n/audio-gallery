import math
import typing

import numpy
import pylab


DTYPE = numpy.dtype("int16")
__MAX_INT = pylab.np.iinfo(DTYPE.type).max


def silence(sample_rate: int = 44100, duration_ms: int = 500) -> typing.List[int]:
    return [0] * int(duration_ms * (sample_rate / 1000.0))


def sinewave(freq, sample_rate: int = 44100, duration_ms: int = 500, volume: float = 1) -> typing.List[int]:
    number_of_samples = duration_ms * (sample_rate / 1000.0)
    return [volume * math.sin(2 * math.pi * freq * (x / sample_rate)) * __MAX_INT for x in range(int(number_of_samples))]


def generate_audio() -> numpy.array:
    return numpy.array(sinewave(4000, volume=0.25) + silence() + sinewave(8000, volume=0.5) + silence()
                       + sinewave(12000, volume=0.75), dtype=DTYPE)
