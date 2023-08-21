import React, { Fragment } from "react";
import { Button } from "react-bootstrap";

import { useLabels } from "../../hooks";

const DataCardLabelButtons = ({ cardData, fn }) => {
    const { data: labels } = useLabels();

    if (!labels) return null;

    return (
        <Fragment>
            <div className="toolbar-gap" />
            {labels.labels.map(label => (
                <Button
                    key={label.name}
                    onClick={() => {
                        fn({ ...cardData, selectedLabelID: label.pk });
                    }}
                    variant="primary"
                >
                    {label["name"]}
                </Button>
            ))}
        </Fragment>
    );
};

export default DataCardLabelButtons;
