#!/usr/bin/env bash


while ! nc -z db 5432; do sleep 3; done
echo "db is up"
while ! nc -z memcached 11211; do sleep 3; done
echo "memcached is up"
while ! nc -z rabbit 5672; do sleep 3; done
echo "rabbit is up"


chown ${APP_USER}:${APP_USER} -R ${APP_ROOT}/${APP_NAME}/source/

chown -R $APP_USER:$APP_USER /opt/audio-gallery/media
su -s /bin/bash -c "mkdir -p /opt/audio-gallery/media/files /opt/audio-gallery/media/spectrum" $APP_USER
su -s /bin/bash -c "mkdir -p /opt/audio-gallery/media/spectrograms  /opt/audio-gallery/media/waveforms" $APP_USER
chown -R $APP_USER:$APP_USER /opt/audio-gallery/logs

cd $APP_ROOT/$APP_NAME/source

if [ "$IS_WORKER" = true ] ; then
    su -s /bin/bash -c "python3 manage.py makemigrations" $APP_USER
    su -s /bin/bash -c "python3 manage.py migrate" $APP_USER

    # create admin user if not yet created
    su -s /bin/bash -c "echo \"from django.contrib.auth.models import User; \
    User.objects.create_superuser('admin', '', '$ADMIN_USER_PASSWORD')\
    if not User.objects.filter(username='admin') else None \" | python3 manage.py shell" $APP_USER

    su -s /bin/bash -c "celery -A audio_gallery purge -f" $APP_USER
    su -s /bin/bash -c "celery -A audio_gallery worker -l info --logfile $DJANGO_LOGS_DIR/celery.log" $APP_USER
else
    sleep 60 # let the worker finish the makemigrations and migrate command
    NODE_MODULES_DIR=$APP_ROOT/$APP_NAME/source/audio_profiling/static/node_modules
    # celery workers do not need node modules
    su -s /bin/bash -c "if [ -d \"$APP_ROOT/node_modules\" ]; then \
        if [ -d \"$NODE_MODULES_DIR\" ]; then \
            rm -r $NODE_MODULES_DIR; \
        fi; \
        mv $APP_ROOT/node_modules $NODE_MODULES_DIR; \
     fi" $APP_USER

    su -s /bin/bash -c "django-admin compilemessages" $APP_USER

    python3 manage.py collectstatic --noinput

    su -s /bin/bash -c "gunicorn audio_gallery.wsgi:application --name audio_gallery \
    --bind 0.0.0.0:8000 --access-logfile $DJANGO_LOGS_DIR/access.log --error-logfile $DJANGO_LOGS_DIR/error.log" $APP_USER
fi
