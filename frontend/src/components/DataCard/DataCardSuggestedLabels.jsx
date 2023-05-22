import React from "react";
import { Spinner } from "react-bootstrap";

import { useSuggestedLabels } from "../../hooks";
import { H4 } from "../ui";

const DataCardSuggestedLabels = ({ card, fn }) => {
    const { data: suggestions } = useSuggestedLabels(card.data);

    if (!suggestions) {
        return (
            <div>
                <Spinner animation="border" role="status" />
                <span className="visually-hidden">Loading labels...</span>
            </div>
        );
    }

    return (
        <div>
            <H4>Suggested Labels</H4>
            <div className="align-items-start d-flex flex-column">
                {suggestions.suggestions.map((suggestion, index) => (
                    <button
                        className="suggested-label unstyled-button"
                        key={index}
                        onClick={() => fn({ dataID: card.id, labelID: suggestion.pk, oldLabelID: card.labelID })}
                    >
                        {`${suggestion.name}: ${suggestion.description}`}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default DataCardSuggestedLabels;
