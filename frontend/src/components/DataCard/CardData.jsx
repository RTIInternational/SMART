import React, { Fragment, useState } from "react";
import {
    Button,
    Modal,
    OverlayTrigger,
    Tooltip
} from "react-bootstrap";

import DataCardMetadata from "./DataCardMetadataOld";

const CardData = ({ card, onSkip, onUnassign, showAdjudicate = true }) => {
    return (
        <div className="cardface-info">
            {showAdjudicate && (
                <div className="card-title" style={{ display: "flex", justifyContent: 'flex-end' }}>
                    {drawSkipQueueButton(card, onUnassign)}
                    {drawSkipButton(card, onSkip)}
                </div>
            )}
            <div className="card-data">
                <h4>Text to Label</h4>
                <p style={{ whiteSpace: "normal" }}>{card.text["text"] || card.text["data"]}</p>
            </div>
            <DataCardMetadata card={card} />
        </div>
    );
};

export default CardData;

// TODO (IR&D): Migrate to DataCardAdjudicateButton
const drawSkipButton = (card, onSkip) => {
    const [isOpen, setIsOpen] = useState(false);
    const [message, setMessage] = useState("");

    const handleSkip = (event) => {
        event.preventDefault();
        onSkip(card, message);
    };

    return (
        <Fragment>
            <OverlayTrigger
                placement="top"
                overlay={
                    <Tooltip id="skip_tooltip">
                        Clicking this button will send this
                        card to an administrator for review
                    </Tooltip>
                }
            >
                
                <Button
                    className="ajucate-button"
                    onClick={() => setIsOpen(true)}
                    variant="info"
                >
                    Adjudicate
                </Button>
            </OverlayTrigger>
            
            <Modal style={{ opacity: 1 }} show={isOpen} onHide={() => setIsOpen(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Adjudicate</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p>Please enter the reasons for skipping this card:</p>
                    <form onSubmit={handleSkip}>
                        <textarea className="adjudicate-message-textarea" onChange={(event) => setMessage(event.target.value)} placeholder="Reasons for skipping..." required />
                        <Button variant="primary" type="submit">Adjudicate</Button>
                    </form>
                </Modal.Body>
            </Modal>
        </Fragment>
    );
};

// TODO (IR&D): Make DataCardSkipButton
const drawSkipQueueButton = (card, onUnassign) => {
    if (!onUnassign) return null;

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
                    onClick={() => onUnassign(card)}
                    style={{ marginRight: "0.25rem" }}
                    variant="info"
                >
                    Skip
                </Button>
            </OverlayTrigger>
        </Fragment>
    );
};
