import React from "react";
import { Spinner } from "react-bootstrap";

import { useLabels, useSuggestedLabels } from "../../hooks";
import { H4 } from "../ui";

const DataCardSuggestedLabels = ({ cardData, fn }) => {
    const { data: labels } = useLabels();
    const { data: suggestions } = useSuggestedLabels(cardData.text);

    if (!labels) return null;

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
                        onClick={() => {
                            // temporary stand-in for spread operator, should be fn({ ...cardData, selectedLabelID: suggestion.pk })
                            const newCardData = Object.assign({}, cardData, { selectedLabelID: suggestion.pk });
                            fn(newCardData);
                        }}                    
                    >
                        {`${suggestion.name}: ${suggestion.description}`}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default DataCardSuggestedLabels;
