#!/bin/bash
# This script initializes the Django project. It will be executed (from 
# supervisord) every time the Docker image is run.



if [ ! -f src/pickmybruin/keys.py ]; then
  echo "SECRET_KEY = '"$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)"'" > src/pickmybruin/keys.py
  echo $(pwd)"/src/pickmybruin/keys.py generated"
fi


#echo "from django.contrib.auth.models import User; if not User.objects.all().exists(): User.create_superuser('root', 'root@localhost', password='password')" | python3 src/manage.py shell

python3 src/manage.py collectstatic --noinput
python3 src/manage.py makemigrations
python3 src/manage.py migrate --noinput

echo "Starting up server on 0.0.0.0:8000"
python3 src/manage.py runserver 0.0.0.0:8000
