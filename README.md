# SMART

This application is for intelligently labeling data by utilizing active learning.  It consists of a Django web application backed by a Postgres database and a Redis store.  The application uses Docker in development to aid in dependency management.

## Development

### Docker containers

This project uses `docker` containers organized by `docker-compose` to ease dependency management in development.  All dependencies are controlled through docker.

#### Initial Startup

First, install docker and docker-compose. Then navigate to `envs/[dev|prod]` and run `docker-compose build` to build all the images.

Next, crate the docker volumes where persistent data will be stored.  `docker volume create --name=vol_smart_pgdata` and `docker volume create --name=vol_smart_data`.

#### Workflow During Development

Run `docker-compose up` to start all docker containers.  This will start up the containers in the foreground so you can see the logs.  If you prefer to run the containers in the background use `docker-compose up -d`. When switching between branches there is no need to run any additional commands (except build if there is dependency change).

If there is ever a dependency change than you will need to re-build the containers using the following commands:

```shell
docker-compose build <container with new dependency>
docker-compose rm <container with new dependency>
docker-compose up
```

If your database is blank, you will need to run migrations to initialize all the required schema objects; you can start a blank backend container and run the migration django management command with the following command:

```shell
docker-compose run --rm smart_backend ./migrate.sh
```

The various services will be available on your machine at their standard ports, but you can override the port numbers if they conflict with other running services. For example, you don't want to run SMART's instance of Postgres on port 5432 if you already have your own local instance of Postgres running on port 5432. To override a port, create a file named `.env` in the `envs/dev` directory that looks something like this:

``` shell
# Default is 5432
EXTERNAL_POSTGRES_PORT=5433

# Default is 3000
EXTERNAL_FRONTEND_PORT=3001
```

The `.env` file is ignored by `.gitignore`.

### Running backend tests

Before running tests locally, be sure your container is rebuilt to contain pytest and the latest tests by using `docker-compose build smart_backend`.

Backend tests use [py.test](https://docs.pytest.org/en/latest/).  To run them, use the following `docker-compose` command:

```
docker-compose run --rm smart_backend ./run_tests.sh
```

Use `py.test -h` to see all the options, but a few useful ones are highlighted below:

 - `-x`: Stop running after the first failure
 - `-s`: Print stdout from the test run (allows you to see temporary print statements in your code)
 - `-k <expression>`: Only run tests with names containing "expression"; you can use Python expressions for more precise control.  See `py.test -h` for more info
 - `--reuse-db`: Don't drop/recreate the database between test runs.  This is useful for for reducing test runtime.  You must not pass this flag if the schema has changed since the last test run.
