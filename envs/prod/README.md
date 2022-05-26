# Production Deployment

This directory is intended to be used in the staging and production environments.

## Backup of Postgres DB

Backups of the postgres DB are automatically generated. The frequency of backups can be changed in [docker-compose.yml](docker-compose.yml) by updating the `SCHEDULE` parameter. The backup files are stored in `backup`, which is only available locally. The backup workflow design is based on [postgres-backup-local](https://github.com/prodrigestivill/docker-postgres-backup-local).

### Manual Backup

If needing to perform a manual backup, you can use the `backup.sh` with this command:

```
docker run --rm -v "$PWD:/backups" -u "$(id -u):$(id -g)" -e POSTGRES_HOST=postgres -e POSTGRES_DB=dbname -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password  prodrigestivill/postgres-backup-local /backup.sh
```

### Restore from Backup

If needing to restore the database to the most recent backup, run the following:

```
./restore-prod.sh
```

## Development

The `build-prod.sh` script is intended to be used for development purposes when you want to restart, rebuild, AND delete existing volumes and databases. Use with caution in a production environment.
