import React from "react";
import {
    Button,
    Tooltip,
    OverlayTrigger
} from "react-bootstrap";

export default function CardData({ card, onSkip }) {
    return (
        <div className="cardface-info">
            <div className="card-title" style={{ display: "flex", justifyContent: 'flex-end' }}>
                {drawSkipButton(card, onSkip)}
            </div>
            <div className="card-data">
                <h4>Text to Label</h4>
                <p>{card.text["text"] || card.text["data"]}</p>
            </div>
            {extractMetadata(card)}
        </div>
    );
}

function drawSkipButton(card, onSkip) {
    return (
        <OverlayTrigger
            placement="top"
            overlay={
                <Tooltip id="skip_tooltip">
                    Clicking this button will send this
                    document to an administrator for review
                </Tooltip>
            }
        >
            <Button
                className="ajucate-button"
                onClick={() => onSkip(card)}
                variant="info"
            >
                Adjudicate
            </Button>
        </OverlayTrigger>
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
