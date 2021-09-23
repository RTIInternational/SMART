import React, { useMemo } from 'react';
import {
    Button,
    ButtonToolbar,
    Tooltip,
    OverlayTrigger
} from "react-bootstrap";
import Select from "react-dropdown-select";

import CardData from '../DataCard/CardData';
import SuggestedLabels from '../DataCard/SuggestedLabels';

export default function AnnotateCard({ card, labels, onSelectLabel, onSkip }) {
    const labelsOptions = useMemo(() => labels.map(label => ({
        value: label["pk"],
        dropdownLabel: `${label["name"]} ${label["description"] !== '' ? '(' + label["description"] + ')' : ''}`
    })));

    return (
        <div className="cardface clearfix">
            <div className="cardface-datacard">
                <CardData card={card} />
                <SuggestedLabels card={card} labels={labels} />
            </div>
            
            <ButtonToolbar className="btn-toolbar">
                {labels.length > 5 ? (
                    <Select
                        className="align-items-center flex py-1 px-2"
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
                ) : (
                    labels.map(opt => (
                        <Button
                            onClick={() => onSelectLabel(card, opt["pk"])}
                            variant="primary"
                            key={`deck-button-${opt["name"]}`}
                        >
                            {opt["name"]}
                        </Button>
                    ))
                )}
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
            </ButtonToolbar>
        </div>
    );
}

export function buildCard(id, start_time, text) {
    return {
        id,
        start_time,
        text
    };
}
