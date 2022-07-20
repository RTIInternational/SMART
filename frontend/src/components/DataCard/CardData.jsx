import React, { Fragment, useState } from "react";
import {
    Button,
    Modal,
    Tooltip,
    OverlayTrigger
} from "react-bootstrap";

export default function CardData({ card, onSkip, onUnassign, showAdjudicate = true }) {
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
                <p>{card.text["text"] || card.text["data"]}</p>
            </div>
            {extractMetadata(card)}
        </div>
    );
}

function drawSkipButton(card, onSkip) {
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
}

function drawSkipQueueButton(card, onUnassign) {
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
}

function extractMetadata(card) {
    if (card.text["metadata"].length == 0) {
        return <p></p>;
    } else {
        return (
            <div className="card-metadata">
                <h4>Background Data</h4>
                {card.text["metadata"].map(val => (
                    <p key={val}>{val}</p>
                ))}
            </div>
        );
    }
}
