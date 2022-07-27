import json
import os

import pandas as pd
from django.conf import settings
from django.core.exceptions import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import InterfaceError

from core.models import ExternalDatabase, Label, MetaDataField
from core.utils.util import upload_data
from core.utils.utils_form import clean_data_helper


def get_connection(db_type, connection_dict):
    """Connect to a database given connection information."""
    if db_type == "microsoft":
        try:
            engine_database = create_engine(
                f"mssql+pyodbc://{connection_dict['username']}:{connection_dict['password']}"
                + f"@{connection_dict['host']}:{connection_dict['port']}/"
                + f"{connection_dict['dbname']}?driver={connection_dict['driver']}"
            )
            return engine_database
        except Exception as e:
            raise ValidationError(
                f"ERROR: database connection failed with the following error -  {str(e)}"
            )
    else:
        raise ValueError(f"ERROR: database type {db_type} is invalid")


def test_login(db_type, engine_database, schema, table):
    """Attempts to login with given connection."""
    try:
        # Perform a no-op
        pd.read_sql(f"SELECT NULL FROM {schema}.{table}", con=engine_database)
    except InterfaceError as e:
        # Catch login fail, may need to handle specific connection errors per database type in the future
        if db_type == "microsoft":
            error_code = e.__context__.args[0]
            if error_code == "28000":
                # Msft login failure
                raise ValidationError("Login to database failed")
            else:
                raise ValidationError(
                    f"ERROR: database connection failed with the following error - {str(e)}"
                )


def test_connection(engine_database, schema, table):
    """Try pulling from a specific table to check that it works."""
    try:
        pd.read_sql(
            sql=f"SELECT COUNT('Text') FROM {schema}.{table}",
            con=engine_database,
        )
    except Exception as e:
        raise ValidationError(
            f"ERROR: database connection failed with the following error - {str(e)}"
        )


def test_schema_exists(engine_database, schema):
    """Check if the given schema exists in the database."""
    schema_set = pd.read_sql(
        sql=f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema}'",
        con=engine_database,
    )
    if len(schema_set) == 0:
        raise ValidationError(f"ERROR: schema {schema} not found in the database.")


def check_if_table_exists(engine_database, schema, table):
    """Check if the given table exists in the database."""
    table_set = pd.read_sql(
        sql=f"SELECT table_name FROM information_schema.tables WHERE "
        f"table_schema = '{schema}' AND table_name = '{table}'",
        con=engine_database,
    )
    if len(table_set) == 0:
        return False
    else:
        return True


def get_full_table(engine_database, schema, table):
    """Read in a table from a database."""
    try:
        return pd.read_sql(
            sql=f"SELECT * FROM {schema}.{table}",
            con=engine_database,
        )
    except Exception as e:
        raise ValidationError(
            f"ERROR: pulling the ingest table failed with the following error - {str(e)}"
        )


def save_external_db_file(connection_dict, project_pk):
    """Given the database credentials for a project, save that information in a file to
    be used later."""
    file_name = "project_" + str(project_pk) + "_db_connection.json"
    os.makedirs(settings.ENV_FILE_PATH, exist_ok=True)

    fpath = os.path.join(settings.ENV_FILE_PATH, file_name)
    with open(fpath, "w") as outputFile:
        json.dump(connection_dict, outputFile)
    return file_name


def load_external_db_file(project_pk):
    """Given the project id, load the external DB file that was previously saved."""
    file_name = "project_" + str(project_pk) + "_db_connection.json"
    fpath = os.path.join(settings.ENV_FILE_PATH, file_name)
    with open(fpath, "r") as inputFile:
        connection_dict = json.load(inputFile)
    return connection_dict


def delete_external_db_file(project_pk):
    """Given the project id, delete the external db file."""
    file_name = "project_" + str(project_pk) + "_db_connection.json"
    fpath = os.path.join(settings.ENV_FILE_PATH, file_name)
    os.remove(fpath)


def load_ingest_table(project, response):
    """This function imports all data from an existing database connection."""
    if not project.has_database_connection():
        response["error"] = "Project does not have a database connection."
    else:
        # check that the project has a database connection and ingest tables
        connection_dict = load_external_db_file(project.pk)
        external_db = ExternalDatabase.objects.get(project=project)

        if not external_db.has_ingest:
            response["error"] = "Project does not have ingest connections set up."
        else:
            # pull the ingest table
            try:
                engine_database = get_connection(
                    external_db.database_type, connection_dict
                )

                # pull the full database table
                data = get_full_table(
                    engine_database,
                    external_db.ingest_schema,
                    external_db.ingest_table_name,
                )
                # clean it using the form validation tool
                cleaned_data = clean_data_helper(
                    data,
                    Label.objects.filter(project=project).values_list(
                        "name", flat=True
                    ),
                    project.dedup_on,
                    project.dedup_fields,
                    MetaDataField.objects.filter(project=project).values_list(
                        "field_name", flat=True
                    ),
                )
                # add the data to the project
                num_added = upload_data(
                    cleaned_data,
                    project,
                    project.queue_set.get(type="normal"),
                    project.queue_set.get(type="irr"),
                    batch_size=project.batch_size,
                )
                response["num_added"] = num_added
            except Exception as e:
                # return errors in the validation tool
                response["error"] = str(e)
    return response
