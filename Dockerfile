FROM ubuntu:16.04

ENV APP_USER audio_stats
ENV APP_ROOT /src
ENV APP_NAME audio-gallery

RUN groupadd -r ${APP_USER} \
    && useradd -r -m \
    --home-dir ${APP_ROOT} \
    -s /usr/sbin/nologin \
    -g ${APP_USER} ${APP_USER}

ARG DEBIAN_FRONTEND=noninteractive

# this way of installing packages is not ideal (generates more layers)
# but for now the flexibilty and readibility is more important for me
RUN apt-get update
#to avoid warning "debconf: delaying package configuration, since apt-utils is not installed":
#see https://github.com/phusion/baseimage-docker/issues/319 for details
RUN apt-get install -y apt-utils
#for models.ImageField
RUN apt-get install -y libjpeg-dev
#for pylab:
RUN apt-get install -y cython
#for avconv:
RUN apt-get install -y libav-tools ffmpeg
#for waveform:
RUN apt-get install -y git libgroove-dev libpng-dev zlib1g-dev make
#for django:
RUN apt-get install -y python3 python3-pip
#python3-tk is needed because without it error is thrown when importing pylab:
#import pylab ImportError: No module named '_tkinter', please install the python3-tk package
RUN apt-get install -y python3-tk
#gettext for django-admin compilemessages
#otherwise this error is thrown: CommandError: Can't find msgfmt. Make sure you have GNU gettext tools 0.15 or newer installed.
RUN apt-get install -y gettext
# for checking other services availibility inside .docker-entrypoint.sh
RUN apt-get install -y netcat-openbsd

RUN apt-get install -y apt-transport-https #http://askubuntu.com/questions/165676/how-do-i-fix-a-e-the-method-driver-usr-lib-apt-methods-http-could-not-be-foun
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update && apt-get install -y yarn


USER ${APP_USER}
#install waveform
RUN git clone https://github.com/andrewrk/waveform.git ${APP_ROOT}/waveform
RUN cd ${APP_ROOT}/waveform && git checkout tags/2.0.0 && make
USER root
RUN ln -s ${APP_ROOT}/waveform/waveform /usr/local/bin/waveform


#install required python packages
USER ${APP_USER}
COPY requirements.txt ${APP_ROOT}/
USER root
RUN pip3 install -r ${APP_ROOT}/requirements.txt
RUN rm ${APP_ROOT}/requirements.txt

WORKDIR ${APP_ROOT}
USER ${APP_USER}
# TODO commit package.json and yarn.lock
RUN yarn add chroma-js@1.2.2
RUN yarn add enquire.js@2.1.5
#wavesurfer 1.3.7 (newest version) is bugged - issue: https://github.com/katspaugh/wavesurfer.js/issues/1055
RUN yarn add wavesurfer.js@1.1.1
RUN yarn add admin-lte@2.3.11


USER root
WORKDIR ${APP_ROOT}

#using bash -c $ENV_VARIABLE because of https://github.com/docker/docker/issues/4783
ENTRYPOINT ["bash","-c","$APP_NAME/source/docker-entrypoint.sh"]
