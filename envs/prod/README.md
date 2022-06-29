# Production Deployment

This directory is intended to be used in the staging and production environments.

## Backup of Postgres DB

Backups of the postgres DB are managed with crontab. The following should be used on the production server by
someone with sudo permission to access the crontab:
```
sudo su
crontab -e
```

The following lines should be in the crontab. Adjust the MAILTO to an email inbox that will receive errors when the cronjob fails. The default below will backup the postgres database every 4 hours. Note that `/home/applications/SMART/envs/prod/backups/` must exist.
```
MAILTO="<email>"
0 */4 * * * docker exec -t prod_postgres_1 pg_dumpall -c -U postgres > /home/applications/SMART/envs/prod/backups/postgres_backup.sql
```

### Manual Backup

If needing to perform a manual backup, you can use this command:

```
docker exec -t prod_postgres_1 pg_dumpall -c -U postgres > /home/applications/SMART/envs/prod/backups/postgres_backup.sql
```

### Restore from Backup

If want to restore the database, run the following:

```
./rebuild.sh
```

## Scheduled Ingest of new Database Data into Projects

Some projects may wish to ingest new data regularly from their ingest database. SMART has provided a management command which will pull new data for all projects with an ingest database set up which have selected the "Enable scheduled ingest" option in the database form.

The following command may be added to the cron file above to ingest new data daily at noon.

```
0 12 * * * docker exec -it backend python manage.py ingest_database_data
```

### Manual Ingest

If needing to perform a manual ingest, you can use this command:

```
docker exec -it backend python manage.py ingest_database_data
```

## Development

The `build-prod.sh` script is intended to be used for development purposes when you want to restart, rebuild, AND delete existing volumes and databases. Use with caution in a production environment.
