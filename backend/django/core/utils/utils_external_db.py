import pandas as pd
from django.core.exceptions import ValidationError
from sqlalchemy import create_engine


def get_connection(db_type, connection_dict):
    """"""
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


def test_connection(engine_database, schema, table):
    try:
        pd.read_sql(
            sql=f"SELECT COUNT('Text') FROM {schema}.{table}",
            con=engine_database,
        )
    except Exception as e:
        raise ValidationError(
            f"ERROR: database connection failed with the following error - {str(e)}"
        )


def get_full_table(engine_database, schema, table):
    try:
        return pd.read_sql(
            sql=f"SELECT * FROM {schema}.{table}",
            con=engine_database,
        )
    except Exception as e:
        raise ValidationError(
            f"ERROR: pulling the ingest table failed with the following error - {str(e)}"
        )
