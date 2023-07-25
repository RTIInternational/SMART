import React from "react";
import { Button, ButtonToolbar } from "react-bootstrap";

import { useLabels } from "../../hooks";

const DataCardLabelButtons = ({ card, fn }) => {
    const { data: labels } = useLabels();

    if (!labels) return null;

    return (
        <ButtonToolbar className="btn-toolbar">
            <div className="toolbar-gap" />
            {labels.labels.map(label => (
                <Button
                    key={label.name}
                    onClick={() => fn({ dataID: card.id, labelID: label.pk, oldLabelID: card.labelID, startTime: card.start_time })}
                    variant="primary"
                >
                    {label["name"]}
                </Button>
            ))}
        </ButtonToolbar>
    );
};

export default DataCardLabelButtons;
