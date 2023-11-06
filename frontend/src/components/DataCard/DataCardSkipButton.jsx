import React, { Fragment } from "react";
import { Button, OverlayTrigger, Tooltip } from "react-bootstrap";

const DataCardSkipButton = ({ cardData, fn }) => {
    return (
        <Fragment>
            <OverlayTrigger
                placement="top"
                overlay={
                    <Tooltip id="skip_tooltip">
                        Clicking this button will skip this card for later.
                    </Tooltip>
                }
            >
                
                <Button
                    className="ajucate-button"
                    onClick={() => fn(cardData)}
                    style={{ marginRight: "0.25rem" }}
                    variant="info"
                >
                    Skip
                </Button>
            </OverlayTrigger>
        </Fragment>
    );
};

export default DataCardSkipButton;
