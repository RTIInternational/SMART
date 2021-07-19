import csv
import io
import os
import tempfile
import zipfile

from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes

from core.models import Project
from core.permissions import IsAdminOrCreator
from core.utils.util import get_labeled_data


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
    data = data.to_dict("records")

    buffer = io.StringIO()
    wr = csv.DictWriter(
        buffer, fieldnames=["ID", "Text", "Label"], quoting=csv.QUOTE_ALL
    )
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
