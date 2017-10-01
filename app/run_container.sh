#!/bin/bash

# Apply database migrations
python manage.py migrate 

# run container
gunicorn config.wsgi -w 3 -b 0.0.0.0:8000 --log-file=- --log-level=info --access-logfile=-
