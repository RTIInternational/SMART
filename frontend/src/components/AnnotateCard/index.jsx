import React from 'react';
import {
    Button,
    ButtonToolbar,
    Tooltip,
    OverlayTrigger
} from "react-bootstrap";
import Select from "react-dropdown-select";

import CardData from '../DataCard/CardData';
import SuggestedLabels from '../DataCard/SuggestedLabels';

export default function AnnotateCard({ card, labels, onSelectLabel, readonly = false, onSkip = null, onDiscard = null, onUnassign = null, showAdjudicate = true, suggestions = true }) {
    return (
        <div className="cardface clearfix">
            <div className="cardface-datacard">
                <CardData card={card} onSkip={onSkip} onUnassign={onUnassign} showAdjudicate={showAdjudicate} />
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
