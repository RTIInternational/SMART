# SMART

This application is for intelligently labeling data by utilizing active learning.  It consists of a Django web application backed by a Postgres database and a Redis store.  The application uses Docker in development to aid in dependency management.

## Development

### Docker containers

This project uses `docker` containers organized by `docker-compose` to ease dependency management in development.  All dependencies other than the app server itself (i.e., postgres and redis) are controlled through docker.

First, install docker and docker-compose; you can then run `docker-compose up -d` in the repository root to start all docker images.

The various services will be available on your machine at their standard ports, but you can override the port numbers if they conflict with other running services. For example, you don't want to run SMART's instance of Postgres on port 5432 if you already have your own local instance of Postgres running on port 5432. To override a port, create a file named `.env` in the `envs/dev` directory that looks something like this:

``` shell
# Default is 5432
EXTERNAL_POSTGRES_PORT=5433

# Default is 3000
EXTERNAL_FRONTEND_PORT=3001
```

The `.env` file is ignored by `.gitignore`.

### App server

The Django app server runs directly on your development machine to avoid having to constantly rebuild a container when front-end/back-end requirements change.  First, set up a virtual environment; then, activate it and install dependencies with the following:

    pip install -r requirements.txt

Also ensure `npm` is installed and run the following to build front-end assets:

    npm run build

And run database migrations (you can run any additional `manage.py` commands this way as well):

    npm run manage.py migrate

You should then be able to run the Django server like so:

    npm run dev
