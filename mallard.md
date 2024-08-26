# Mallard Staging Environment

Mallard is the RTI-internal staging environment for SMART. This project lives at `/projects/SMART`, and can be updated by using git. It is easiest to edit code on mallard using VS Code Remote SSH. To have permission to edit the files, you must be added to the `cds` group on mallard.

The `mallard` branch of this repository contains a few changes necessary to run SMART on mallard, mainly port mappings.

## Upgrading Postgres and Migrating Data

These instructions are based on upgrading Postgres from 9 to 15 in the SMART staging environment, maintaining the existing data. Postgres changed its default password hashing method, but we kept the old one (`md5`) for compatibility in this environment.

1. `docker compose down`
2. Edit the `docker-compose.yml` file to add a volume to the postgres service:
```
      - ./smartapp:/smartapp
```
3. `docker compose up -d postgres`
4. `docker exec prod_postgres_1 bash -c "pg_dumpall -d smart -U smart -h localhost > /smartapp/data.sql"`
5. `docker compose down`
6. Edit the `docker-common.yml` file and replace `- smart_pgdata:/var/lib/postgresql/data` with `- smart_pgdata_15_2:/var/lib/postgresql/data`
7. Edit the `docker-common.yml` file and replace `image: postgres:9.6.2` with `image: postgres:15.2`
8. Edit the `docker-common.yml` and add the environment variable `- POSTGRES_HOST_AUTH_METHOD=md5`
9. `docker container ls | grep postgres` then `docker rm` any matching containers
10. `docker rmi postgres:9.6.2`
11. `docker compose up -d postgres`
12. `docker exec prod_postgres_1 bash -c "pg_dumpall -d smart -U smart -h localhost < /smartapp/data.sql"`
13. `docker compose down`
14. `docker compose up`

### Cleanup

After verifying that the new Postgres version is working, you can remove the old volume by editing the `docker-compose.yml` file and removing the `./smartapp:/smartapp` line from the postgres service. Then `rm -fr ./smartapp` and `docker volume rm smart_pgdata`.
