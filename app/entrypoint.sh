#!/usr/bin/env bash

# environment variables that can be set to control this entrypoint:
#   DJANGO_COLLECTSTATIC
#   DJANGO_MIGRATE
#   DJANGO_COLLECTSTATIC_LEADERONLY
#   DJANGO_MIGRATE_LEADERONLY

# Detect whether the container is denoted as a "leader"
# For multi-instance deployments, create /tmp/leader/is_leader (volume mount
# can be used) to denote the single container that should run admin commands

if [ -f /tmp/leader/is_leader ]; then
    IS_LEADER=1
    echo "Leader marker detected"
fi

# Run collectstatic command if either:
# - DJANGO_COLLECTSTATIC is present
# - Leader marker detected and DJANGO_COLLECTSTATIC_LEADERONLY is present

if [[ $DJANGO_COLLECTSTATIC || ( $IS_LEADER && $DJANGO_COLLECTSTATIC_LEADERONLY) ]]; then
    echo "Running Django collectstatic"
    python manage.py collectstatic -c --noinput
else
    echo "Skipping Django collectstatic"
fi

# Run migrate command if either:
# - DJANGO_MIGRATE is present
# - Leader marker detected and DJANGO_MIGRATE_LEADERONLY is present

if [[ $DJANGO_MIGRATE || ( $IS_LEADER && $DJANGO_MIGRATE_LEADERONLY) ]]; then
    echo "Running Django migrate"
    python manage.py migrate --noinput
else
    echo "Skipping Django migrate"
fi

# Run launch command based on first argument:
# "web" or no first argument: creates web container running with gunicorn
# "runserver": creates web container running with 'python manage.py runserver'
# If needed, can be extended to handle arguments like:
# "worker": creates celery worker
# "beat": creates celery beat scheduler

if [ "$1" = "web" ] || [ "$1" = "gunicorn" ] || [ -z "$1" ]; then
    echo "Starting web container with gunicorn ..."
    /usr/local/bin/gunicorn config.wsgi:application -w 2 -b :8000 --log-level=info --log-file - --access-logfile -
elif [ "$1" = "runserver" ]; then
    echo "Starting web container with python manage.py runserver ..."
    python manage.py runserver 0.0.0.0:8000
else
    # run arbitrary command
    $@
fi
