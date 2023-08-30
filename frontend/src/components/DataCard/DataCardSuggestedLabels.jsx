import React, { Fragment, useState } from "react";
import { Spinner } from "react-bootstrap";

import { useLabels, useSuggestedLabels } from "../../hooks";
import { H4 } from "../ui";
import ConfirmationModal from "./ConfirmationModal";

const DataCardSuggestedLabels = ({ cardData, fn, includeModal }) => {
    const [selectedLabelID, setSelectedLabelID] = useState(null);
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
                    <Fragment key={index} >
                        <button
                            className="suggested-label unstyled-button"
                            onClick={() => {
                                if (includeModal) setSelectedLabelID(suggestion.pk);
                                else fn({ ...cardData, selectedLabelID: suggestion.pk }); 
                            }}                    
                        >
                            {`${suggestion.name}: ${suggestion.description}`}
                        </button>
                        <ConfirmationModal 
                            showModal={selectedLabelID === suggestion.pk}
                            setSelectedLabelID={setSelectedLabelID}
                            fn={ () => {
                                fn({ ...cardData, selectedLabelID });
                            }}
                        />
                    </Fragment>
                ))}
            </div>
        </div>
    );
};

export default DataCardSuggestedLabels;
