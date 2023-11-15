import React, { Fragment, useState } from "react";
import { Button } from "react-bootstrap";

import { useLabels } from "../../hooks";
import ConfirmationModal from "./ConfirmationModal";

const DataCardLabelButtons = ({ cardData, fn, includeModal }) => {
    const [selectedLabelID, setSelectedLabelID] = useState(null);
    const { data: labels } = useLabels();

    if (!labels) return null;


    return (
        <Fragment>
            <div className="toolbar-gap" />
            {labels.labels.map(label => (
                <Fragment key={label.name}>
                    <Button
                        onClick={() => {
                            if (includeModal) setSelectedLabelID(label.pk);
                            else fn({ ...cardData, selectedLabelID: label.pk });
                        }}
                        variant="primary"
                    >
                        {label["name"]}
                    </Button>
                    <ConfirmationModal 
                        showModal={selectedLabelID === label.pk}
                        setSelectedLabelID={setSelectedLabelID}
                        fn={ () => {
                            fn({ ...cardData, selectedLabelID });
                        }}
                    />
                </Fragment>
            ))}
        </Fragment>
    );
};

export default DataCardLabelButtons;
