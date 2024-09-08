import numpy as np
from django.core.exceptions import ValidationError

from core.utils.util import md5_hash


def clean_data_helper(
    data, supplied_labels, dedup_on, dedup_fields, metadata_fields=None
):

    # correct for differences in capitalization
    for col in data.columns:
        for field, field_lower in zip(["Text", "Label", "ID"], ["text", "label", "id"]):
            if col != field and col == field_lower:
                data.rename(columns={col: field}, inplace=True)

    if "Text" not in data.columns:
        raise ValidationError("Data is missing required field 'Text'.")

    if "Label" not in data.columns:
        data["Label"] = None

    if len(data) < 1:
        raise ValidationError("Data is empty.")

    lower_cols = [c.lower() for c in data.columns]
    if len(lower_cols) > len(set(lower_cols)):
        raise ValidationError(
            "There are duplicate fields in this file. To avoid confusion "
            "SMART requires all fields to have unique names."
        )

    found_metadata_fields = [
        c for c in data.columns if c not in ["Text", "Label", "ID"]
    ]

    # this option is only true if we're adding data to an existing project
    if (
        metadata_fields is not None
        and len(metadata_fields) > 0
        and (set(metadata_fields) != set(found_metadata_fields))
    ):
        raise ValidationError(
            "There were metadata fields provided in the "
            "initial data upload that are missing from this data."
            f" Original fields: {', '.join(metadata_fields)}."
            f" Found fields: {', '.join(found_metadata_fields)}."
        )

    # validating the dedup list being sent
    if dedup_on == "Text_Some_Metadata" and len(dedup_fields) == 0:
        raise ValidationError(
            "The 'Text and Metadata fields'"
            " option was selected but no metadata fields were specified."
        )

    if len(dedup_fields) > 0:
        dedup_list = [
            d.strip() for d in dedup_fields.strip().split(";") if len(d.strip()) > 0
        ]
        if metadata_fields is not None:
            compare_list = metadata_fields
        else:
            compare_list = found_metadata_fields

        # if there is no metadata then there can't be dedup fields
        if len(set(dedup_list) - set(compare_list)) > 0:
            raise ValidationError(
                "The dedup fields specified should be a subset of"
                " the data's provided metadata fields. "
                f"Dedup fields: {dedup_list},"
                f" Metadata fields: {compare_list}"
            )

    labels_in_data = data["Label"].dropna(inplace=False).unique()
    if len(labels_in_data) > 0 and len(set(labels_in_data) - set(supplied_labels)) > 0:
        just_in_data = set(labels_in_data) - set(supplied_labels)
        raise ValidationError(
            f"There are extra labels in the file which were not created in step 2: {just_in_data}"
        )

    if "ID" in data.columns:
        # there should be no null values
        if data["ID"].isnull().sum() > 0:
            raise ValidationError("Unique ID field cannot have missing values.")

        data_lens = data["ID"].astype(str).apply(lambda x: len(x))
        # check that the ID follow the character limit
        if np.any(np.greater(data_lens, [128] * len(data_lens))):
            raise ValidationError(
                "Unique ID should not be greater than 128 characters."
            )

        data["id_hash"] = data["ID"].astype(str).apply(md5_hash)
        # they have an id column, check for duplicates
        if len(data["id_hash"].tolist()) > len(data["id_hash"].unique()):
            raise ValidationError("Unique ID provided contains duplicates.")

    return data


def clean_label_data_helper(data, existing_labels=[]):
    # correct for differences in capitalization
    required_fields = ["Label", "Description"]
    data.rename({c: c.lower().capitalize() for c in data.columns}, inplace=True)
    for field in required_fields:
        if field not in data.columns:
            raise ValidationError(f"File is missing required field '{field}'.")

    new_labels = list(set(data["Label"].unique()) - set(existing_labels))
    if len(new_labels) > 0 and len(existing_labels) > 0:
        raise ValidationError(
            f"New labels were found in this file: {', '.join(new_labels)}"
        )

    if len(data) < 2 and len(existing_labels) == 0:
        raise ValidationError("At least two labels are required.")

    lower_cols = [c.lower() for c in data.columns]
    if len(lower_cols) > len(set(lower_cols)):
        raise ValidationError(
            "There are duplicate fields in this file. To avoid confusion "
            "SMART requires all fields to have unique names."
        )

    if len(data["Label"].unique()) < len(data):
        label_counts = data["Label"].value_counts()
        label_counts = label_counts.loc[label_counts > 1]
        raise ValidationError(
            f"ERROR: labels must be unique. The following labels appear more than once: {', '.join(label_counts.index.tolist())}"
        )

    return data
