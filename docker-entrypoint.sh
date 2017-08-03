#!/usr/bin/env bash

chown ${APP_USER}:${APP_USER} -R ${APP_ROOT}/${APP_NAME}/source/

su -s /bin/bash -c "if [ -d \"$APP_ROOT/node_modules\" ]; then \
    mv $APP_ROOT/node_modules $APP_ROOT/$APP_NAME/source/audio_profiling/static; \
fi" $APP_USER

chown -R $APP_USER:$APP_USER /opt/audio-gallery/media
su -s /bin/bash -c "mkdir -p /opt/audio-gallery/media/files /opt/audio-gallery/media/spectrum" $APP_USER
su -s /bin/bash -c "mkdir -p /opt/audio-gallery/media/spectrograms  /opt/audio-gallery/media/waveforms" $APP_USER
chown -R $APP_USER:$APP_USER /opt/audio-gallery/logs
chown -R $APP_USER:$APP_USER /opt/audio-gallery/database

su -s /bin/bash -c "python3 $APP_NAME/source/manage.py makemigrations" $APP_USER
su -s /bin/bash -c "python3 $APP_NAME/source/manage.py migrate" $APP_USER


cd $APP_ROOT/$APP_NAME/source
su -s /bin/bash -c "django-admin compilemessages" $APP_USER
cd $APP_ROOT


if [ "$CREATE_ADMIN_USER" = true ] ; then \
    su -s /bin/bash -c "echo \"from django.contrib.auth.models import User; \
    User.objects.create_superuser('admin', '', '$ADMIN_USER_PASSWORD')\
    if not User.objects.filter(username='admin') else None \" | \
    python3 ${APP_ROOT}/${APP_NAME}/source/manage.py shell" $APP_USER; \
fi


cd $APP_NAME/source
python3 manage.py collectstatic --noinput
su -s /bin/bash -c "celery -A audio_gallery purge -f" $APP_USER
su -s /bin/bash -c "celery -A audio_gallery worker -l info --logfile $DJANGO_LOGS_DIR/celery.log \
   &> /dev/null &" $APP_USER
su -s /bin/bash -c "gunicorn audio_gallery.wsgi:application --name audio_gallery \
  --bind 0.0.0.0:8000 --access-logfile $DJANGO_LOGS_DIR/access.log --error-logfile $DJANGO_LOGS_DIR/error.log" $APP_USER
