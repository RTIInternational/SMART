import React, { Fragment, useState } from 'react';
import {
    Button,
    ButtonToolbar,
    Modal,
    Tooltip,
    OverlayTrigger
} from "react-bootstrap";
import Select from "react-dropdown-select";

import CardData from '../DataCard/CardData';
import SuggestedLabels from '../DataCard/SuggestedLabels';

export default function AnnotateCard({ card, labels, onSelectLabel, readonly = false, onSkip = null, onDiscard = null, suggestions = true }) {
    return (
        <div className="cardface clearfix">
            <div className="cardface-datacard">
                <CardData card={card} onSkip={onSkip} />
                {suggestions && labels.length > 5 && (
                    <SuggestedLabels card={card} labels={labels} onSelectLabel={onSelectLabel} />
                )}
            </div>
            
            { !readonly && drawEditOptions(card, labels, onSelectLabel, onSkip, onDiscard) }
        </div>
    );
}

function drawEditOptions(card, labels, onSelectLabel, onSkip, onDiscard) {
    const labelsOptions = labels.map(label => ({
        value: label["pk"],
        dropdownLabel: `${label["name"]} ${label["description"] !== '' ? '(' + label["description"] + ')' : ''}`
    }));

    return (
        <ButtonToolbar className="btn-toolbar">
            <div className="toolbar-gap" />
            {labels.length > 5 ? (
                drawLabelSelect(card, labelsOptions, onSelectLabel)
            ) : (
                drawLabelButtons(card, labels, onSelectLabel)
            )}
            { onDiscard != null && drawDiscardButton(card, onDiscard) }
        </ButtonToolbar>
    );
}

function drawLabelSelect(card, labelsOptions, onSelectLabel) {
    return (
        <Select
            className="align-items-center flex py-1 px-2 annotate-select"
            dropdownHandle={false}
            labelField="dropdownLabel"
            onChange={(value) => {
                onSelectLabel(card, value[0].value);
            }}
            options={labelsOptions}
            placeholder="Select label..."
            searchBy="dropdownLabel"
            sortBy="dropdownLabel"
        />
    );
}

function drawLabelButtons(card, labels, onSelectLabel) {
    return (
        labels.map(opt => (
            <Button
                onClick={() => onSelectLabel(card, opt["pk"])}
                variant="primary"
                key={`deck-button-${opt["name"]}`}
            >
                {opt["name"]}
            </Button>
        ))
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

function drawDiscardButton(card, onDiscard) {
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
                key={`discard_${card.id}`}
                onClick={() => onDiscard(card.id)}
                variant="danger"
            >
                Discard
            </Button>
        </OverlayTrigger>
    );
}

export function buildCard(id, start_time, text) {
    return {
        id,
        start_time,
        text
    };
}
