# ALOSI adaptive engine web application
This repo subfolder contains a Django web application the runs the ALOSI adaptive engine.

## Running the engine application locally

### Install prerequisites:
* [Docker](https://docs.docker.com/install/)

### Setup application for local development:

```
# clone the repo locally
git clone https://github.com/harvard-vpal/adaptive-engine

# change into app directory
cd app

# build Docker images and start up application in background
docker-compose up -d

# apply database migrations
docker-compose run web python manage.py migrate
```

The engine should now be available at localhost:8000. Try opening localhost:8000/engine/api in a web browser.

## Application Configuration
### Creating a superuser
To access the Django admin panel, a superuser needs to be created.
```
# Open an interactive shell in engine docker container
docker-compose run web bash

# Create super user account
python manage.py createsuperuser

# ... answer the prompts ...

# Ctrl-D to exit shell when finished

```

### API Token generation
1. Open admin panel (localhost:8000/admin) and log in with user credentials

2. Create a new Token model associated with user (Token -> Add Token). An API token will be auto-generated in the 
`key` field of the new model.


## Running tests
```
docker-compose run web pytest
```

## Running model update
There is a custom django-admin command to update the engine model. One approach for automating the model update is to 
set up a cron job. Here's an example that runs the custom command via Docker (assumes the image is named "app", and
uses custom settings located in `config/settings/eb_prod.py`) that updates the model every 2 hours:
```
0 */2 * * * docker run app python manage.py update_model --eta=0.0 --M=20.0 --settings=config.settings.eb_prod
```
