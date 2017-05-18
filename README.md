# SMART

This application is for intelligently labeling data by utilizing active learning.  It consists of a Django web application backed by a Postgres database and a Redis store.  The application uses Docker in development to aid in dependency management.

## Development

### Docker containers

This project uses `docker` containers organized by `docker-compose` to ease dependency management in development.  All dependencies other than the app server itself (i.e., postgres and redis) are controlled through docker.

First, install docker and docker-compose; you can then run `docker-compose up -d` in the repository root to start all docker images.  Postgres will be available on port 5433 of your machine (to avoid annoying conflicts with Postgres.app already on port 5432), and redis will be on port 6379.

### App server

The Django app server runs directly on your development machine to avoid having to constantly rebuild a container when front-end/back-end requirements change.  First, set up a virtual environment; then, activate it and install dependencies with the following:

    pip install -r requirements.txt

Also ensure `npm` is installed and run the following to build front-end assets:

    npm run build

And run database migrations (you can run any additional `manage.py` commands this way as well):

    npm run manage.py migrate

You should then be able to run the Django server like so:

    npm run dev
