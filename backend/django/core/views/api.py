import csv
import io
import os
import tempfile
import zipfile

import pandas as pd
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.forms import clean_data_helper
from core.models import ExternalDatabase, Label, MetaDataField, Project
from core.permissions import IsAdminOrCreator
from core.templatetags import project_extras
from core.utils.util import get_labeled_data, upload_data
from core.utils.utils_external_db import (
    check_if_table_exists,
    get_connection,
    get_full_table,
    load_external_db_file,
)


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def download_data(request, project_pk):
    """This function gets the labeled data and makes it available for download.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        an HttpResponse containing the requested data
    """
    project = Project.objects.get(pk=project_pk)
    data, labels = get_labeled_data(project)
    fieldnames = data.columns.values.tolist()
    data = data.to_dict("records")

    buffer = io.StringIO()
    wr = csv.DictWriter(buffer, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    wr.writeheader()
    wr.writerows(data)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="text/csv")
    response["Content-Disposition"] = "attachment;"

    return response


@api_view(["GET"])
@permission_classes((IsAdminOrCreator,))
def download_model(request, project_pk):
    """This function gets the labeled data and makes it available for download.

    Args:
        request: The POST request
        pk: Primary key of the project
    Returns:
        an HttpResponse containing the requested data
    """
    project = Project.objects.get(pk=project_pk)

    # https://stackoverflow.com/questions/12881294/django-create-a-zip-of-multiple-files-and-make-it-downloadable
    zip_subdir = "model_project" + str(project_pk)

    tfidf_path = os.path.join(
        settings.TF_IDF_PATH, "project_" + str(project_pk) + "_tfidf_matrix.pkl"
    )
    tfidf_vectorizer_path = os.path.join(
        settings.TF_IDF_PATH, "project_" + str(project_pk) + "_vectorizer.pkl"
    )
    readme_path = os.path.join(settings.BASE_DIR, "core", "data", "README.pdf")
    dockerfile_path = os.path.join(settings.BASE_DIR, "core", "data", "Dockerfile")
    requirements_path = os.path.join(
        settings.BASE_DIR, "core", "data", "requirements.txt"
    )
    start_script_path = os.path.join(
        settings.BASE_DIR, "core", "data", "start_notebook.sh"
    )
    usage_examples_path = os.path.join(
        settings.BASE_DIR, "core", "data", "UsageExamples.ipynb"
    )
    current_training_set = project.get_current_training_set()
    model_path = os.path.join(
        settings.MODEL_PICKLE_PATH,
        "project_"
        + str(project_pk)
        + "_training_"
        + str(current_training_set.set_number - 1)
        + ".pkl",
    )

    data, label_data = get_labeled_data(project)
    # open the tempfile and write the label data to it
    temp_labeleddata_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, dir=settings.DATA_DIR
    )
    temp_labeleddata_file.seek(0)
    data.to_csv(temp_labeleddata_file.name, index=False)
    temp_labeleddata_file.flush()
    temp_labeleddata_file.close()

    temp_label_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, dir=settings.DATA_DIR
    )
    temp_label_file.seek(0)
    label_data.to_csv(temp_label_file.name, index=False)
    temp_label_file.flush()
    temp_label_file.close()

    s = io.BytesIO()
    # open the zip folder
    zip_file = zipfile.ZipFile(s, "w")
    for path in [
        tfidf_path,
        tfidf_vectorizer_path,
        readme_path,
        model_path,
        temp_labeleddata_file.name,
        temp_label_file.name,
        dockerfile_path,
        requirements_path,
        start_script_path,
        usage_examples_path,
    ]:
        fdir, fname = os.path.split(path)
        if path == temp_label_file.name:
            fname = "project_" + str(project_pk) + "_labels.csv"
        elif path == temp_labeleddata_file.name:
            fname = "project_" + str(project_pk) + "_labeled_data.csv"
        # write the file to the zip folder
        zip_path = os.path.join(zip_subdir, fname)
        zip_file.write(path, zip_path)
    zip_file.close()

    response = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
    response["Content-Disposition"] = "attachment;"

    return response


@api_view(["POST"])
@permission_classes((IsAdminOrCreator,))
def import_database_table(request, project_pk):
    """This function imports all data from an existing database connection.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        {}
    """
    response = {}
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)

    # Make sure coder is an admin
    if project_extras.proj_permission_level(project, profile) > 1:

        if not project.has_database_connection():
            response["error"] = "Project does not have a database connection."
        else:
            # check that the project has a database connection and ingest tables
            connection_dict = load_external_db_file(project_pk)
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
                        cleaned_data, project, batch_size=project.batch_size
                    )
                    response["num_added"] = num_added
                except Exception as e:
                    # return errors in the validation tool
                    response["error"] = str(e)
    else:
        response["error"] = "Invalid credentials. Must be an admin."

    if "error" in response.keys():
        return Response(response, status=status.HTTP_404_NOT_FOUND)

    return Response(response)


@api_view(["POST"])
@permission_classes((IsAdminOrCreator,))
def export_database_table(request, project_pk):
    """This function exports labeled data to an existing database connection.

    Args:
        request: The POST request
        project_pk: Primary key of the project
    Returns:
        {}
    """
    response = {}
    profile = request.user.profile
    project = Project.objects.get(pk=project_pk)

    # Make sure coder is an admin
    if project_extras.proj_permission_level(project, profile) > 1:

        if not project.has_database_connection():
            response["error"] = "Project does not have a database connection."
        else:
            # check that the project has a database connection and export tables
            connection_dict = load_external_db_file(project_pk)
            external_db = ExternalDatabase.objects.get(project=project)

            if not external_db.has_export:
                response["error"] = "Project does not have export connections set up."
            else:
                try:
                    engine_database = get_connection(
                        external_db.database_type, connection_dict
                    )
                    table_name_string = (
                        f"{external_db.export_schema}.{external_db.export_table_name}"
                    )

                    # pull all labeled data
                    data, labels = get_labeled_data(project)
                    if len(data) > 0:

                        # pull the export table
                        if check_if_table_exists(
                            engine_database,
                            external_db.export_schema,
                            external_db.export_table_name,
                        ):
                            response[
                                "success_message"
                            ] = "Appending labeled data to existing table."

                            # Only upload new data. Deduping on upload ID, since duplicate contents
                            # are deduped when the data is first added
                            existing_ids = pd.read_sql(
                                sql=f"SELECT DISTINCT ID FROM {table_name_string}",
                                con=engine_database,
                            )["ID"].tolist()
                            data = data.loc[~data["ID"].isin(existing_ids)]
                            if len(data) > 0:
                                data.to_sql(
                                    name=external_db.export_table_name,
                                    con=engine_database,
                                    schema=external_db.export_schema,
                                    if_exists="append",
                                    index=False,
                                )

                        else:
                            response[
                                "success_message"
                            ] = "Creating new table in database."
                            # create table with columns from labeled data
                            data.to_sql(
                                name=external_db.export_table_name,
                                con=engine_database,
                                schema=external_db.export_schema,
                                if_exists="fail",
                                index=False,
                            )
                    response[
                        "success_message"
                    ] += f" Added {len(data)} rows to the database."

                except Exception as e:
                    # return errors in the validation tool
                    response["error"] = str(e)
    else:
        response["error"] = "Invalid credentials. Must be an admin."

    if "error" in response.keys():
        return Response(response, status=status.HTTP_404_NOT_FOUND)

    return Response(response)
