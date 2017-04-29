from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from . import models


class CategoryAdmin(TranslationAdmin):
    pass


class AudioPageAdmin(TranslationAdmin):
    pass


class AudioFileAdmin(admin.ModelAdmin):
    readonly_fields = ('waveform', 'mp3', 'spectrogram', 'spectrum')


admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.AudioPage, AudioPageAdmin)
admin.site.register(models.AudioFile, AudioFileAdmin)
