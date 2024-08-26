import hashlib
import os
from io import StringIO
from itertools import combinations

import numpy as np
import pandas as pd
import pytz
from celery import chord
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone
from sentence_transformers import SentenceTransformer

from core import tasks
from core.models import (
    AssignedData,
    Data,
    DataLabel,
    DataQueue,
    IRRLog,
    Label,
    LabelEmbeddings,
    MetaData,
    MetaDataField,
    Profile,
    Project,
    ProjectPermissions,
    RecycleBin,
    TrainingSet,
    VerifiedDataLabel,
    LabelMetaDataField,
    LabelMetaData,
    Category,
)
from core.utils.utils_queue import fill_queue
from smart.settings import TIME_ZONE_FRONTEND

# from string_grouper import compute_pairwise_similarities


# https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
# Disable warning for false positive warning that should only trigger on chained assignment
pd.options.mode.chained_assignment = None  # default='warn'

# Using a prebuilt model
# How this model was built: https://github.com/dsteedRTI/csv-to-embeddings-model
# Sbert Model can be found here: https://www.sbert.net/docs/pretrained_models.html
# Sbert Model Card: https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-dot-v1
model_path = "core/smart_embeddings_model"
embeddings_model = SentenceTransformer(model_path)


def md5_hash(obj):
    """Return MD5 hash hexdigest of obj; returns None if obj is None."""
    if obj is not None:
        if isinstance(obj, int):
            obj = str(obj)
        return hashlib.md5(obj.encode("utf-8", errors="ignore")).hexdigest()
    else:
        return None


def create_profile(username, password, email):
    """Create a user with the given attributes.

    Create a user in Django's authentication model and link it to our own project user
    model.
    """
    user = get_user_model().objects.create(
        username=username, password=password, email=email
    )

    return Profile.objects.get(user=user)


def create_project(name, creator, percentage_irr=10, num_users_irr=2, classifier=None):
    """Create a project with the given name and creator."""
    if classifier:
        proj = Project.objects.create(
            name=name,
            creator=creator,
            percentage_irr=percentage_irr,
            num_users_irr=num_users_irr,
            classifier=classifier,
        )
    else:
        proj = Project.objects.create(
            name=name,
            creator=creator,
            percentage_irr=percentage_irr,
            num_users_irr=num_users_irr,
        )
    TrainingSet.objects.create(project=proj, set_number=0)

    return proj


def upload_data(form_data, project, queue=None, irr_queue=None, batch_size=30):
    """Perform data upload given validated form_data.

    1. Add data to database
    2. If new project then fill queue (only new project will pass queue object)
    3. Save the uploaded data file
    4. Create tf_idf file
    5. Check and Trigger model
    """

    new_df = add_data(project, form_data)

    # only fill the queues if the queues are empty.
    num_in_queues = 0
    if queue:
        num_in_queues += DataQueue.objects.filter(queue_id=queue.id).count()
    if irr_queue:
        num_in_queues += DataQueue.objects.filter(queue_id=irr_queue.id).count()
    if queue and num_in_queues == 0:
        fill_queue(
            queue=queue,
            irr_queue=irr_queue,
            orderby="random",
            irr_percent=project.percentage_irr,
            batch_size=batch_size,
        )

    # Celery and emebeddings wasn't working well together...
    # transaction.on_commit(
    #     lambda: tasks.send_label_embeddings_task.apply_async(
    #         kwargs={"project_pk": project.pk}
    #     )
    # )
    tasks.send_label_embeddings_task(project.pk)

    # Since User can upload Labeled Data and this data is added to current training_set
    # we need to check_and_trigger model.  However since training model requires
    # tf_idf to be created we must create a chord which garuntees that tfidf
    # creation task is completed before check and trigger model task

    if len(new_df) > 0:
        save_data_file(new_df, project.pk)
        if project.classifier is not None:
            transaction.on_commit(
                lambda: chord(
                    tasks.send_tfidf_creation_task.s(project.pk),
                    tasks.send_check_and_trigger_model_task.si(project.pk),
                ).apply_async()
            )
    return len(new_df)


def create_data_from_csv(df, project):
    """Insert data objects into database using cursor.copy_from by creating an in-memory
    tsv representation of the data."""
    columns = ["Text", "project", "hash", "ID", "id_hash", "irr_ind"]
    stream = StringIO()

    df["project"] = project.pk
    df["irr_ind"] = False

    # Replace tabs since thats our delimiter, remove carriage returns since copy_from doesnt like them
    # escape all backslashes because it seems to fix "end-of-copy marker corrupt"
    df["Text"] = (
        df["Text"]
        .astype(str)
        .apply(
            lambda x: x.replace("\t", " ")
            .replace("\r", " ")
            .replace("\n", " ")
            .replace("\\", "\\\\")
        )
    )

    df.to_csv(stream, sep="\t", header=False, index=False, columns=columns)
    stream.seek(0)

    with connection.cursor() as c:
        c.copy_from(
            stream,
            Data._meta.db_table,
            sep="\t",
            null="",
            columns=[
                "text",
                "project_id",
                "hash",
                "upload_id",
                "upload_id_hash",
                "irr_ind",
            ],
        )


def create_labels_from_csv(df, project):
    """Insert DataLabel objects into database using cursor.copy_from by creating an in-
    memory tsv representation of the datalabel objects."""
    columns = [
        "label_id",
        "data_id",
        "profile_id",
        "training_set_id",
        "time_to_label",
        "timestamp",
        "pre_loaded",
    ]
    stream = StringIO()

    labels = {label.name: label.pk for label in project.labels.all()}
    df["data_id"] = df["hash"].apply(
        lambda x: Data.objects.get(hash=x, project=project).pk
    )
    df["time_to_label"] = None
    df["timestamp"] = None
    df["training_set_id"] = project.get_current_training_set().pk
    df["label_id"] = df["Label"].apply(lambda x: labels[x])
    df["profile_id"] = project.creator.pk

    # these data are preloaded
    df["pre_loaded"] = True

    df.to_csv(stream, sep="\t", header=False, index=False, columns=columns)
    stream.seek(0)

    with connection.cursor() as c:
        c.copy_from(
            stream, DataLabel._meta.db_table, sep="\t", null="", columns=columns
        )


def create_metadata_objects_from_csv(df, project):
    """Insert metadata objects into database."""
    metadataFields = MetaDataField.objects.filter(project=project)
    data_objects = pd.DataFrame(
        list(Data.objects.filter(project=project).values("id", "hash"))
    )
    df = df.merge(data_objects, on="hash", how="left")

    for meta in metadataFields:
        field_name = str(meta)
        df_meta = df[["id", field_name]].rename(
            columns={field_name: "value", "id": "data_id"}
        )
        df_meta["value"] = df_meta["value"].fillna("")
        df_meta["metadata_field_id"] = meta.pk

        stream = StringIO()
        df_meta.to_csv(
            stream,
            sep="\t",
            header=False,
            index=False,
            columns=df_meta.columns.values.tolist(),
        )
        stream.seek(0)
        with connection.cursor() as c:
            c.copy_from(
                stream,
                MetaData._meta.db_table,
                sep="\t",
                null="",
                columns=df_meta.columns.values.tolist(),
            )


def generate_label_embeddings(project):
    """Create embeddings for each description of label."""

    project_labels = Label.objects.filter(project=project)

    if len(project_labels) > 5:
        project_labels_descriptions = list(
            project_labels.values_list("description", flat=True)
        )

        # Make manual embeddings. Prod settings made calling the api from the backend infeasible
        embeddings = embeddings_model.encode(project_labels_descriptions)

        # We have to use tolist() since not calling API now to handle numpy arrays
        # (JSON response from API originally handled this for us)
        label_embeddings = [
            LabelEmbeddings(embedding=embedding.tolist(), label=label)
            for embedding, label in zip(embeddings, project_labels)
        ]
        LabelEmbeddings.objects.bulk_create(
            label_embeddings, ignore_conflicts=True, batch_size=8000
        )


def update_label_embeddings(project):
    """Update embeddings for each description of label."""

    project_labels = Label.objects.filter(project=project)

    if len(project_labels) > 5:
        project_labels_descriptions = list(
            project_labels.values_list("description", flat=True)
        )
        project_labels_ids = list(project_labels.values_list("id", flat=True))

        # Make manual embeddings. Prod settings made calling the api from the backend infeasible
        embeddings = embeddings_model.encode(project_labels_descriptions)

        project_labels_embeddings = LabelEmbeddings.objects.filter(
            label_id__in=project_labels_ids
        )

        # We have to use tolist() since not calling API now to handle numpy arrays
        # (JSON response from API originally handled this for us)
        for embedding, label_embedding in zip(embeddings, project_labels_embeddings):
            label_embedding.embedding = embedding.tolist()

        LabelEmbeddings.objects.bulk_update(
            project_labels_embeddings, ["embedding"], batch_size=8000
        )


def add_data(project, df):
    """Add data to an existing project.

    df should be two column dataframe with columns Text and Label.  Label can be empty
    and should have at least one null value.  Any row that has Label should be added to
    DataLabel
    """
    # Create hash of (text + dedup fields). So each unique combination should have a different hash
    dedup_on_fields = MetaDataField.objects.filter(
        project=project, use_with_dedup=True
    ).values_list("field_name", flat=True)

    df["hash"] = ""
    for f in dedup_on_fields:
        df["hash"] += df[f].astype(str) + "_"

    df["hash"] += df["Text"].astype(str)
    df["hash"] = df["hash"].apply(md5_hash)

    df.drop_duplicates(subset=["hash"], keep="first", inplace=True)

    # check that the data is not already in the system and drop duplicates
    df = df.loc[
        ~df["hash"].isin(
            list(Data.objects.filter(project=project).values_list("hash", flat=True))
        )
    ]

    if len(df) == 0:
        return []

    # Limit the number of rows to 2mil for the entire project
    num_existing_data = Data.objects.filter(project=project).count()
    if num_existing_data >= 2000000:
        return []

    df = df[: 2000000 - num_existing_data]

    # if there is no ID column already, add it and hash it
    df.reset_index(drop=True, inplace=True)
    if "ID" not in df.columns:
        # need to check what ID's are already in the data in case a previous upload DID have IDs
        existing_ids = Data.objects.filter(project=project).values_list(
            "upload_id", flat=True
        )

        # build a list of integers for the IDs. Skip any IDs already in use
        counter = num_existing_data - 1
        new_id_list = []
        while len(new_id_list) < len(df):
            counter += 1
            if counter in existing_ids:
                continue
            new_id_list.append(counter)

        # should add to what already exists
        df["ID"] = new_id_list
        df["id_hash"] = df["ID"].astype(str).apply(md5_hash)
    else:
        # get the hashes from existing identifiers. Check that the new identifiers do not overlap
        existing_hashes = Data.objects.filter(project=project).values_list(
            "upload_id_hash", flat=True
        )
        df = df.loc[~df["id_hash"].isin(existing_hashes)]

        if len(df) == 0:
            return []

    # Create the data objects
    create_data_from_csv(df.copy(deep=True), project)
    create_metadata_objects_from_csv(df.copy(deep=True), project)

    # Find the data that has labels
    labeled_df = df[~pd.isnull(df["Label"])]
    if len(labeled_df) > 0:
        create_labels_from_csv(labeled_df, project)

    return df


def perc_agreement_table_data(project):
    """Takes in the irrlog and finds the pairwise percent agreement."""
    irr_data = set(
        IRRLog.objects.filter(data__project=project).values_list("data", flat=True)
    )

    user_list = [
        str(Profile.objects.get(pk=x))
        for x in list(
            ProjectPermissions.objects.filter(project=project).values_list(
                "profile", flat=True
            )
        )
    ]
    user_list.append(str(project.creator))
    user_pk_list = list(
        ProjectPermissions.objects.filter(project=project).values_list(
            "profile__pk", flat=True
        )
    )
    user_pk_list.append(project.creator.pk)
    # get all possible pairs of users
    user_combinations = combinations(user_list, r=2)
    data_choices = []

    for d in irr_data:
        d_log = IRRLog.objects.filter(data=d, data__project=project)

        # get the percent agreement between the users  = (num agree)/size_data
        if d_log.count() < 2:
            # don't use this datum, it isn't processed yet
            continue
        temp_dict = {}
        for user in user_pk_list:
            if d_log.filter(profile=user).count() == 0:
                temp_dict[str(Profile.objects.get(pk=user))] = np.nan
            else:
                d = d_log.get(profile=user)
                if d.label is None:
                    name = "Skip"
                else:
                    name = d.label.name
                temp_dict[str(d.profile)] = name
        data_choices.append(temp_dict)
    # If there is no data, just return nothing
    if len(data_choices) == 0:
        user_agree = []
        for pair in user_combinations:
            user_agree.append(
                {
                    "First Coder": pair[0],
                    "Second Coder": pair[1],
                    "Percent Agreement": "No samples",
                }
            )
        return user_agree

    choice_frame = pd.DataFrame(data_choices)
    user_agree = []
    for pair in user_combinations:
        # get the total number they both edited
        p_total = len(choice_frame[[pair[0], pair[1]]].dropna(axis=0))

        # get the elements that were labeled by both and not skipped
        choice_frame2 = (
            choice_frame[[pair[0], pair[1]]].replace("Skip", np.nan).dropna(axis=0)
        )

        # fill the na's so if they are both na they aren't equal
        p_agree = np.sum(np.equal(choice_frame2[pair[0]], choice_frame2[pair[1]]))

        if p_total > 0:
            user_agree.append(
                {
                    "First Coder": pair[0],
                    "Second Coder": pair[1],
                    "Percent Agreement": str(round(100 * (p_agree / p_total), 1)) + "%",
                }
            )
        else:
            user_agree.append(
                {
                    "First Coder": pair[0],
                    "Second Coder": pair[1],
                    "Percent Agreement": "No samples",
                }
            )
    return user_agree


def irr_heatmap_data(project):
    """Takes in the irrlog and formats the data to be usable in the irr heatmap."""
    # get the list of users and labels for this project
    user_list = list(
        ProjectPermissions.objects.filter(project=project).values_list(
            "profile__user", flat=True
        )
    )
    user_list.append(project.creator.pk)
    irr_data = set(IRRLog.objects.values_list("data", flat=True))

    # Initialize the dictionary of dictionaries to use for the heatmap later
    user_label_counts = {}
    for user1 in user_list:
        for user2 in user_list:
            user_label_counts[str(user1) + "_" + str(user2)] = {
                "data": {},
                "labels": set(),
            }

    for data_id in irr_data:
        # iterate over the data and count up labels
        data_log_list = IRRLog.objects.filter(data=data_id, data__project=project)
        small_user_list = data_log_list.values_list("profile__user", flat=True)
        for user1 in small_user_list:
            for user2 in small_user_list:
                user_combo = str(user1) + "_" + str(user2)
                label1 = str(data_log_list.get(profile__pk=user1).label).replace(
                    "None", "Adjudicate"
                )
                user_label_counts[user_combo]["labels"].add(label1)
                label2 = str(data_log_list.get(profile__pk=user2).label).replace(
                    "None", "Adjudicate"
                )
                user_label_counts[user_combo]["labels"].add(label2)
                if label1 not in user_label_counts[user_combo]["data"].keys():
                    user_label_counts[user_combo]["data"][label1] = {}

                if label2 not in user_label_counts[user_combo]["data"][label1].keys():
                    user_label_counts[user_combo]["data"][str(label1)][label2] = 1
                else:
                    user_label_counts[user_combo]["data"][str(label1)][label2] += 1

    # if label combinations didn't occur set them to 0
    for user_combo in user_label_counts.keys():
        for label1 in user_label_counts[user_combo]["labels"]:
            for label2 in user_label_counts[user_combo]["labels"]:
                if label1 not in user_label_counts[user_combo]["data"].keys():
                    user_label_counts[user_combo]["data"][label1] = {}
                if label2 not in user_label_counts[user_combo]["data"][label1].keys():
                    user_label_counts[user_combo]["data"][label1][label2] = 0

    # get the results in the final format needed for the graph
    end_data = {}
    end_data_labels = {}
    for user_combo in user_label_counts:
        end_data_list = []
        end_data_labels[user_combo] = list(user_label_counts[user_combo]["labels"])
        for label1 in user_label_counts[user_combo]["data"]:
            for label2 in user_label_counts[user_combo]["data"][label1]:
                end_data_list.append(
                    {
                        "label1": label1,
                        "label2": label2,
                        "count": user_label_counts[user_combo]["data"][label1][label2],
                    }
                )
        end_data[user_combo] = end_data_list

    return end_data, end_data_labels


def save_data_file(df, project_pk):
    """Given the df used to create and save objects save just the data to a file. Make
    sure to count the number of files in directory assocaited with the project and save
    as next incremented file name.

    Args:
        df: dataframe used to create and save data objects, contains `Text` column
            which has the text data
        project_pk: Primary key of the project
    Returns:
        file: The filepath to the saved datafile
    """
    num_proj_files = len(
        [
            f
            for f in os.listdir(settings.PROJECT_FILE_PATH)
            if f.startswith("project_" + str(project_pk))
        ]
    )
    fpath = os.path.join(
        settings.PROJECT_FILE_PATH,
        "project_" + str(project_pk) + "_data_" + str(num_proj_files) + ".csv",
    )

    df = df[["ID", "Text", "Label"]]
    df.to_csv(fpath, index=False)

    return fpath


def save_codebook_file(data, project_pk):
    """Given the django data file, save it as the codebook for that project make sure to
    overwrite any project that is already there/"""
    date = timezone.now().strftime("%m_%d_%y__%H_%M_%S")
    fpath = os.path.join(
        settings.CODEBOOK_FILE_PATH,
        "project_" + str(project_pk) + "_codebook" + date + ".pdf",
    )
    with open(fpath, "wb") as outputFile:
        outputFile.write(data.read())
    return fpath.replace("/data/code_books/", "")


def get_labeled_data(project, unverified=True):
    """Given a project, get the list of labeled data.

    Args:
        project: Project object
        unverified: bool. If true, then include unverified data in download.
    Returns:
        data: a list of the labeled data
    """
    project_labels = Label.objects.filter(project=project)
    # get the data labels
    data = []
    labels = []
    for label in project_labels:
        labels.append({"Name": label.name, "Label_ID": label.pk})
        labeled_data = DataLabel.objects.filter(label=label, data__irr_ind=False)
        if not unverified:
            labeled_data = labeled_data.filter(verified__isnull=False)
        for d in labeled_data:
            temp = {}
            temp["ID"] = d.data.upload_id
            temp["Text"] = d.data.text
            metadata = MetaData.objects.filter(data=d.data)
            for m in metadata:
                temp[m.metadata_field.field_name] = m.value
            temp["Label"] = label.name
            if d.pre_loaded:
                temp["Pre-Loaded"] = "Yes"
            else:
                temp["Pre-Loaded"] = "No"
            if label.description:
                temp["Description"] = label.description
            temp["Profile"] = str(d.profile.user)
            if d.timestamp:
                temp["Timestamp"] = d.timestamp.astimezone(
                    pytz.timezone(TIME_ZONE_FRONTEND)
                )
            else:
                temp["Timestamp"] = None
            if hasattr(d, "verified"):
                v = VerifiedDataLabel.objects.get(data_label=d)
                temp["Verified"] = "Yes"
                temp["Verified By"] = str(v.verified_by.user)
                temp["Verified Timestamp"] = v.verified_timestamp.astimezone(
                    pytz.timezone(TIME_ZONE_FRONTEND)
                )
            else:
                temp["Verified"] = "No"
                temp["Verified By"] = None
                temp["Verified Timestamp"] = None
            data.append(temp)
    labeled_data_frame = pd.DataFrame(data)
    label_frame = pd.DataFrame(labels)

    return labeled_data_frame, label_frame


def project_status(project):
    """This returns data information.

    Args:
        project
    Returns:
        data: a list of data information
    """
    total_labels = DataLabel.objects.filter(
        data__project=project, data__irr_ind=False
    ).count()

    total_data_objs = project.data_set.all().count()

    final_verified = DataLabel.objects.filter(
        data__project=project, data__irr_ind=False, verified__isnull=False
    ).count()

    final_unverified = DataLabel.objects.filter(
        data__project=project, data__irr_ind=False, verified__isnull=True
    ).count()

    stuff_in_queue = (
        DataQueue.objects.filter(queue__project=project, queue__type="admin")
        .values_list("data__pk", flat=True)
        .count()
    )

    recycle_ids = (
        RecycleBin.objects.filter(data__project=project)
        .values_list("data__pk", flat=True)
        .count()
    )

    assigned_ids = (
        AssignedData.objects.filter(data__project=project)
        .values_list("data__pk", flat=True)
        .count()
    )

    unlabeled_data_objs = get_unlabelled_data_objs(project.id)

    return {
        "adjudication": stuff_in_queue,
        "assigned": assigned_ids,
        "final": total_labels,
        "final_verified": final_verified,
        "final_unverified": final_unverified,
        "recycled": recycle_ids,
        "total": total_data_objs,
        "unlabeled": unlabeled_data_objs,
        "badge": f"{total_labels}/{total_data_objs - recycle_ids}",
    }


def get_projects(self, order_by_folders):
    """Get all projects for a user.

    Args:
        self: from get_context_data/queryset
        order_by_folders: sort projects into folders
    Returns:
        projects: a list of projects
    """
    # Projects profile created
    qs1 = Project.objects.filter(creator=self.request.user.profile)

    # Projects profile has permissions for
    qs2 = Project.objects.filter(projectpermissions__profile=self.request.user.profile)

    qs = qs1 | qs2
    projects = qs.distinct()
    if order_by_folders:
        projects = projects.order_by(self.ordering).reverse()

    return projects


def get_projects_umbrellas(self):
    """Get all projects' folders for a user (sorted alphabetically.)

    Args:
        self: from get_context_data
    Returns:
        projects_umbrellas: a list of projects' folders
    """

    projects = get_projects(self, False)
    return (
        projects.values_list("umbrella_string", flat=True)
        .distinct()
        .order_by("umbrella_string")
    )


def get_unlabelled_data_objs(project_id: int) -> int:
    """Function to retrieve the total count of unlabelled data objects for a project.

    This SQL query is comprised of 5 subqueries, each of which retrieves the ids of
    data objects that are in a particular table. The first sub-query is the total list
    of unlabbeled data entries for a given project, while the remaining four are tables
    that we will be comparing against the list of ids from the first sub-query. The
    remaining four sets of ids are then joined on the `project_ids`. We then return
    the count of the rows that have `null` values.

    Args:
        project_id: The id of the project for which to retrieve the count of unlabelled
            data objects.

    Returns:
        The count of unlabelled data objects for a project.
    """
    query = """
        WITH project_ids AS (
            SELECT cd.id
            FROM core_data cd
            LEFT JOIN core_datalabel cdl ON cd.id = cdl.data_id
            WHERE cd.project_id = %s AND cdl.label_id IS NULL
        ),
        queue_ids AS (
            SELECT cdq.id, cdq.data_id
            FROM core_dataqueue cdq
            LEFT JOIN core_queue cq ON cdq.queue_id = cq.id
            WHERE cq.project_id = %s AND cq.type = 'admin'
        ),
        irr_log_ids AS (
            SELECT ci.id, ci.data_id
            FROM core_irrlog ci
            LEFT JOIN core_data cd ON ci.data_id = cd.id
            WHERE cd.project_id = %s
        ),
        assigned_ids AS (
            SELECT ca.id, ca.data_id
            FROM core_assigneddata ca
            LEFT JOIN core_data cd ON ca.data_id = cd.id
            WHERE cd.project_id = %s
        ),
        recycle_ids AS (
            SELECT cr.id, cr.data_id
            FROM core_recyclebin cr
            LEFT JOIN core_data cd ON cr.data_id = cd.id
            WHERE cd.project_id = %s
        )
        SELECT COUNT(*)
            FROM (
                SELECT p.id
                FROM project_ids p
                LEFT JOIN queue_ids q ON p.id = q.data_id
                LEFT JOIN irr_log_ids irr ON p.id = irr.data_id
                LEFT JOIN assigned_ids a ON p.id = a.data_id
                LEFT JOIN recycle_ids r ON p.id = r.data_id
                WHERE q.id IS NULL
                    AND irr.id IS NULL
                    AND a.id IS NULL
                        AND r.id IS NULL
            ) AS filtered_ids;
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [project_id] * 5)
        return cursor.fetchone()[0]


def create_label_metadata(project, label_data, label_list):
    """This function creates LabelMetadataField objects for each new field and
    LabelMetadata objects for each label-field pair.

    Args:
        project: a Project object
        label_data: a pandas dataframe with the label metadata fields
        label_list: a list of label objects for the project
    """
    label_metadata = [c for c in label_data if c not in ["Label", "Description"]]
    if len(label_metadata) > 0:
        for metadata_col in label_metadata:
            label_metadata_field = LabelMetaDataField.objects.create(
                project=project, field_name=metadata_col
            )
            all_metadata_values = label_data[metadata_col].tolist()
            all_label_metadata_objects = [
                LabelMetaData(
                    label=label_list[i],
                    label_metadata_field=label_metadata_field,
                    value=all_metadata_values[i],
                )
                for i in range(len(all_metadata_values))
            ]
            LabelMetaData.objects.bulk_create(
                all_label_metadata_objects, batch_size=8000
            )


def create_or_update_project_category(project, label_metadata, data_metadata):
    """This function takes a field which overlaps between the label and data metadata
    and sets it to the project category to filter the suggestions by."""
    metadata_both = list(set(data_metadata) & set(label_metadata))
    if len(metadata_both) > 0:
        # by default just pick the first overlap
        if Category.objects.filter(project=project).exists():
            Category.objects.filter(project=project).update(
                field_name=metadata_both[0],
                label_metadata_field=LabelMetaDataField.objects.get(
                    field_name=metadata_both[0], project=project
                ),
                data_metadata_field=MetaDataField.objects.get(
                    field_name=metadata_both[0], project=project
                ),
            )
        else:
            Category.objects.create(
                project=project,
                field_name=metadata_both[0],
                label_metadata_field=LabelMetaDataField.objects.get(
                    field_name=metadata_both[0], project=project
                ),
                data_metadata_field=MetaDataField.objects.get(
                    field_name=metadata_both[0], project=project
                ),
            )


def update_label_descriptions_metadata(project, new_data):
    """This function takes in a dataset with new descriptions and possibly metadata for
    an existing label set and updates both the descriptions and any metadata.

    It adds new metadata if needed and may set project category if not set.
    """
    # get the set of labels in the data
    project_labels = Label.objects.filter(
        project=project, name__in=new_data["Label"].tolist()
    )

    label_dict = new_data.set_index("Label").to_dict()
    for label in project_labels:
        label.description = label_dict["Description"][label.name]
    Label.objects.bulk_update(project_labels, ["description"], batch_size=800)
    update_label_embeddings(project)

    # loop over all metadata fields
    label_metadata = [c for c in new_data if c not in ["Label", "Description"]]
    for metadata_col in label_metadata:
        label_metadata_field, created = LabelMetaDataField.objects.get_or_create(
            project=project, field_name=metadata_col
        )
        if created:
            # create objects for each label in the entire label set
            new_label_metadata_objects = [
                (
                    LabelMetaData(
                        label=label,
                        label_metadata_field=label_metadata_field,
                        value=label_dict[metadata_col][label.name],
                    )
                    if label.name in label_dict[metadata_col].keys()
                    else LabelMetaData(
                        label=label, label_metadata_field=label_metadata_field, value=""
                    )
                )
                for label in Label.objects.filter(project=project)
            ]
            LabelMetaData.objects.bulk_create(
                new_label_metadata_objects, batch_size=8000
            )
        else:
            # update objects for each label, just the ones affected
            existing_metadata_objects = LabelMetaData.objects.filter(
                label__name__in=new_data["Label"].tolist(),
                label_metadata_field=label_metadata_field,
            )
            for m in existing_metadata_objects:
                m.value = label_dict[metadata_col][m.label.name]
            LabelMetaData.objects.bulk_update(
                existing_metadata_objects, ["value"], batch_size=8000
            )

    # check if the project category needs to be updated
    data_metadata = MetaDataField.objects.filter(project=project).values_list(
        "field_name", flat=True
    )
    create_or_update_project_category(project, label_metadata, data_metadata)
