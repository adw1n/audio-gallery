[![Build Status](https://travis-ci.org/adw1n/audio-gallery.svg?branch=master)](https://travis-ci.org/adw1n/audio-gallery)

### Live demo:  
[http://violin-competition.adw1n.com/](http://violin-competition.adw1n.com/)  
This demo is running a slightly older version of the project.


### About
You can only upload audio files that are:
* in a WAV file format
* mono
* 44100Hz

### Browser support
Full support:
* desktop: firefox, chrome, opera, chromium
* mobile: chrome

Partial support - everything works, but the instantaneous spectrum is not refreshed during the audio play (instead the spectrum for the whole audio file is taken):
* the rest of the browsers

### DEPLOYMENT:
You need to have `docker` and `docker-compose` installed. After you have installed both, run those commands:
```bash
sudo mkdir -p /opt/audio-gallery/logs /opt/audio-gallery/static /opt/audio-gallery/media /opt/audio-gallery/pgdata
git clone https://github.com/adw1n/audio-gallery
cd audio-gallery
# modify password (ADMIN_USER_PASSWORD) for your admin account in .django_env
sudo docker-compose build  # this might take about 4 minutes
sudo docker-compose up -d
# give it a minute to get up
# open your browser and go to http://SERVER_IP:8888
# go to the admin panel http://SERVER_IP:8888/admin to set things up
# and log in using credentials:
# user: admin
# password: password from the .django_env file
```

### Customization / configuration
* (**required**) **admin user password** - you **have to modify** this setting for **security reasons** (otherwise if you make this app publicly available anyone will be able to log in using the default credentials)  
  change `ADMIN_USER_PASSWORD` in [.django_env](.django_env)
* (optional/recommended) `ALLOWED_HOSTS` setting in [.django_env](.django_env) file  
* (optional) `ADMIN_MAIL` setting in [.django_env](.django_env) file
* (optional) logos - place two JPGs in [audio_profiling/static/logos/](audio_profiling/static/logos/):
    * logo_small.jpg 50x50px
    * logo.jpg 122x50px
    * depending on your logos' background you might want to change css property of logo's background-color in [logo_settings.css](audio_profiling/static/logo_settings.css) file
* (optional) internalization  
  Project supports two languages out of the box:
    * english
    * polish

  To add support for another language modify `LANGUAGES` variable in [settings.py](audio_gallery/settings.py). After that generate a language file - run  `django-admin makemessages -l de` (where de is your locale name) ([relevant django docs page](https://docs.djangoproject.com/en/1.11/topics/i18n/translation/#message-files)). Add translations to the language file. Deploy the app and add missing translations using the admin panel (/admin).
  
  To remove support for polish language just remove if from `LANGUAGES` variable in [settings.py](audio_gallery/settings.py).

### Backups
Copy `/opt/audio-gallery/media` and `/opt/audio-gallery/pgdata` directories and put them in a single tar/zip archive for each backup.

### License:
This project uses the Unlicense license (see [LICENSE](LICENSE) file).  
**BUT** all the music, graphics (logos, violin photos) etc. on the [demo page](http://violin-competition.adw1n.com/) are **not covered by the license** and belong to the rightful owners.
