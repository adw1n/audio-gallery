#!/usr/bin/env bash

chown -R $APP_USER:$APP_USER /opt/audio-gallery/media
su -s /bin/bash -c "mkdir -p /opt/audio-gallery/media/files /opt/audio-gallery/media/spectrum" $APP_USER
su -s /bin/bash -c "mkdir -p /opt/audio-gallery/media/spectrograms  /opt/audio-gallery/media/waveforms" $APP_USER
chown -R $APP_USER:$APP_USER /opt/audio-gallery/logs
chown -R $APP_USER:$APP_USER /opt/audio-gallery/database

su -s /bin/bash -c "python3 $APP_NAME/source/manage.py makemigrations" $APP_USER
su -s /bin/bash -c "python3 $APP_NAME/source/manage.py migrate" $APP_USER

if [ "$CREATE_ADMIN_USER" = true ] ; then \
    su -s /bin/bash -c "echo \"from django.contrib.auth.models import User; \
    User.objects.create_superuser('admin', '', '$ADMIN_USER_PASSWORD')\
    if not User.objects.filter(username='admin') else None \" | \
    python3 ${APP_ROOT}/${APP_NAME}/source/manage.py shell" $APP_USER; \
fi


service rabbitmq-server start
service memcached start
cd $APP_NAME/source
python3 manage.py collectstatic --noinput
su -s /bin/bash -c "celery purge -f" $APP_USER
su -s /bin/bash -c "celery -A audio_gallery worker -l info --logfile $DJANGO_LOGS_DIR/celery.log --pidfile /tmp/celery.pid \
   &> /dev/null &" $APP_USER
#&" $APP_USER
su -s /bin/bash -c "gunicorn audio_gallery.wsgi:application --name audio_gallery \
  --bind 0.0.0.0:8000 --access-logfile $DJANGO_LOGS_DIR/access.log --error-logfile $DJANGO_LOGS_DIR/error.log" $APP_USER