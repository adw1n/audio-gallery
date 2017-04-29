import modeltranslation.translator

from . import models


class CategoryTranslationOptions(modeltranslation.translator.TranslationOptions):
    fields = ('name',)
    required_languages = {'default': fields}


class AudioPageTranslationOptions(modeltranslation.translator.TranslationOptions):
    fields = ('name', 'description')
    required_languages = {'default': ('name',)}


modeltranslation.translator.translator.register(models.Category, CategoryTranslationOptions)
modeltranslation.translator.translator.register(models.AudioPage, AudioPageTranslationOptions)
