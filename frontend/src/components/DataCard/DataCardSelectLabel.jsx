import React, { useState } from "react";
import Select from "react-dropdown-select";

import { useLabels } from "../../hooks";
import ConfirmationModal from "./ConfirmationModal";


const DataCardSelectLabel = ({ cardData, fn, includeModal }) => {
    const [selectedLabelID, setSelectedLabelID] = useState(null);
    const { data: labels } = useLabels();

    const labelsOptions = labels ? labels.labels.map(label => ({
        value: label["pk"],
        dropdownLabel: `${label["name"]} ${label["description"] !== '' ? '(' + label["description"] + ')' : ''}`
    })) : [];

    return (
        <div className="label-select-wrapper">
            <Select
                className="rounded"
                dropdownHandle={false}
                labelField="dropdownLabel"
                onChange={(value) => {
                    if (includeModal) setSelectedLabelID(value[0].value);
                    else fn({ ...cardData, selectedLabelID: value[0].value });
                }}
                options={labelsOptions}
                placeholder="Select label..."
                searchBy="dropdownLabel"
                sortBy="dropdownLabel"
            />
            <ConfirmationModal 
                showModal={selectedLabelID !== null}
                setSelectedLabelID={setSelectedLabelID}
                fn={ () => {
                    fn({ ...cardData, selectedLabelID });
                }}
            />
        </div>
        
    );
};

export default DataCardSelectLabel;
