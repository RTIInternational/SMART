![SMART](docs/img/smart-banner.png)

[![Build Status](https://travis-ci.com/RTIInternational/SMART.svg?&branch=master)](https://travis-ci.com/RTIInternational/SMART) [![Documentation Status](https://readthedocs.org/projects/smart-app/badge/?version=latest)](https://smart-app.readthedocs.io/en/latest/?badge=latest)

SMART is an open source application designed to help data scientists and research teams efficiently build labeled training datasets for supervised machine learning tasks.

- **[SMART Landing Page](https://rtiinternational.github.io/SMART/)** 
- **[SMART User Documentation](https://smart-app.readthedocs.io/en/latest/#)**

## Development

The simplest way to start developing is to go to the `envs/dev` directory and run the rebuild script with `./rebuild.sh`.  This will: clean up any old containers/volumes, rebuild the images, run all migrations, and seed the database with some testing data.

The testing data includes three users `root`, `user1`, `test_user` and all of their passwords are `password555`. There is also a handful of projects with randomly labeled data by the various users.

### Docker containers

This project uses `docker` containers organized by `docker-compose` to ease dependency management in development.  All dependencies are controlled through docker.

#### Initial Startup

First, install docker and docker-compose. Then navigate to `envs/dev` and run `docker-compose build` to build all the images.

Next, crate the docker volumes where persistent data will be stored.  `docker volume create --name=vol_smart_pgdata` and `docker volume create --name=vol_smart_data`.

### Workflow During Development

Run `docker-compose up` to start all docker containers.  This will start up the containers in the foreground so you can see the logs.  If you prefer to run the containers in the background use `docker-compose up -d`. When switching between branches there is no need to run any additional commands (except build if there is dependency change).

### Dependency Changes

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

### Custom Environment Variables

The various services will be available on your machine at their standard ports, but you can override the port numbers if they conflict with other running services. For example, you don't want to run SMART's instance of Postgres on port 5432 if you already have your own local instance of Postgres running on port 5432. To override a port, create a file named `.env` in the `envs/dev` directory that looks something like this:

``` shell
# Default is 5432
EXTERNAL_POSTGRES_PORT=5433

# Default is 3000
EXTERNAL_FRONTEND_PORT=3001
```

The `.env` file is ignored by `.gitignore`.

### Running tests

Backend tests use [py.test](https://docs.pytest.org/en/latest/) and [flake8](http://flake8.pycqa.org/en/latest/).  To run them, use the following `docker-compose` command from the `env/dev` directory:

```
docker-compose run --rm smart_backend ./run_tests.sh <args>
```

Where `<args>` are arguments to be passed to py.test.  Use `py.test -h` to see all the options, but a few useful ones are highlighted below:

 - `-x`: Stop running after the first failure
 - `-s`: Print stdout from the test run (allows you to see temporary print statements in your code)
 - `-k <expression>`: Only run tests with names containing "expression"; you can use Python expressions for more precise control.  See `py.test -h` for more info
 - `--reuse-db`: Don't drop/recreate the database between test runs.  This is useful for for reducing test runtime.  You must not pass this flag if the schema has changed since the last test run.


Frontend tests use [mocha](https://mochajs.org/api/mocha.js.html) and [eslint](https://eslint.org/docs/user-guide/getting-started).  To run them, use the following `docker-compose` command from the `env/dev` directory:

```
docker-compose run --rm smart_frontend ./run_tests.sh
```

### Contributing

If you would like to contribute to SMART feel free to submit issues and pull requests addressing any bugs or features. Before submitting a pull request make sure to follow the few guidelines below:

* Clearly explain the bug you are experiencing or the feature you wish to implement in the description.
* For new features include unit tests to ensure the feature is working correctly and the new feature is maintainable going forward.
* For bug fixes include unit tests to ensure that previously untested code is now covered.
* Make sure your branch passes all the existing backend and frontend tests.
