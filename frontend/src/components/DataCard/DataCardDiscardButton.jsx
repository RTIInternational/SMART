import React from "react";
import {
    Button,
    Tooltip,
    OverlayTrigger
} from "react-bootstrap";

const DataCardDiscardButton = ({ cardData, fn, show }) => {
    if (!show) return null;
    return (
        <OverlayTrigger
            placement="top"
            overlay={
                <Tooltip id="discard_tooltip">
                    This marks this data as uncodable,
                    and will remove it from the active
                    data in this project.
                </Tooltip>
            }
        >
            <Button
                key={`discard_${cardData.dataID}`}
                onClick={() => fn(cardData.dataID)}
                variant="danger"
            >
                Discard
            </Button>
        </OverlayTrigger>
    );
};

export default DataCardDiscardButton;
