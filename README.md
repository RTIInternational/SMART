# SMART

This application is for intelligently labeling data by utilizing active learning.  It consists of a Django web application backed by a Postgres database and a Redis store.  The application uses Docker in development to aid in dependency management.

## Development

### Docker containers

This project uses `docker` containers organized by `docker-compose` to ease dependency management in development.  All dependencies are controlled through docker.

First, install docker and docker-compose. Then navigate to `envs/[dev|prod]` and run `docker-compose up -d` to start all docker images.

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
docker-compose run --rm smart_backend py.test
```

()

Use `py.test -h` to see all the options, but a few useful ones are highlighted below:

 - `-x`: Stop running after the first failure
 - `-s`: Print stdout from the test run (allows you to see temporary print statements in your code)
 - `-k <expression>`: Only run tests with names containing "expression"; you can use Python expressions for more precise control.  See `py.test -h` for more info
