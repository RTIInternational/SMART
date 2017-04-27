# SMART

This application is for intelligently labeling data by utilizing active learning.  It consists of a Django web application backed by a Postgres database and a Redis store.  The application uses Docker in development to aid in dependency management.

## Development

### Docker containers

This project uses `docker` containers organized by `docker-compose` to ease dependency management in development.  All dependencies other than the app server itself (i.e., postgres and redis) are controlled through docker.

First, install docker and docker-compose; you can then run `docker-compose up -d` in the repository root to start all docker images.  Postgres will be available on port 5433 of your machine (to avoid annoying conflicts with Postgres.app already on port 5432), and redis will be on port 6379.
