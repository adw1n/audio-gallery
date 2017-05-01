from __future__ import absolute_import, unicode_literals
import os
import logging

import celery
import celery.signals



# see http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html for explanation of those settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "audio_gallery.settings")
app = celery.Celery("audio_gallery")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@celery.signals.setup_logging.connect
def task_setup_logging(**kwargs):
    logger = logging.getLogger("celery")
    return logger
