import React from "react";
import Select from "react-dropdown-select";

import { useLabels } from "../../hooks";

const DataCardSelectLabel = ({ cardData, fn }) => {
    const { data: labels } = useLabels();

    const labelsOptions = labels ? labels.labels.map(label => ({
        value: label["pk"],
        dropdownLabel: `${label["name"]} ${label["description"] !== '' ? '(' + label["description"] + ')' : ''}`
    })) : [];

    return (
        <Select
            className="rounded"
            dropdownHandle={false}
            labelField="dropdownLabel"
            onChange={(value) => {
                fn({ ...cardData, selectedLabelID: value[0].value });
            }}
            options={labelsOptions}
            placeholder="Select label..."
            searchBy="dropdownLabel"
            sortBy="dropdownLabel"
        />
    );
};

export default DataCardSelectLabel;
