import React, { Fragment } from "react";
import { Card } from "react-bootstrap";

import DataCardAdjudicateButton from "./DataCardAdjudicateButton";
import DataCardSkipButton from "./DataCardSkipButton";
import DataCardMetadata from "./DataCardMetadataNew";
import DataCardSelectLabel from "./DataCardSelectLabel";
import DataCardSuggestedLabels from "./DataCardSuggestedLabels";
import DataCardText from "./DataCardText";
import { useModifyLabel, useChangeToSkip, useLabels } from "../../hooks";
import DataCardLabelButtons from "./DataCardLabelButtons";

const DataCard = ({ data, type, actions }) => {
    const { data: labels } = useLabels();
    const { mutate: changeToSkip } = useChangeToSkip();
    const { mutate: modifyLabel } = useModifyLabel();
    const allHandlers = {
        changeToSkip,
        modifyLabel,
        actions,
    };
    const cardData = formatDataForCard(data, type);
    const handlers = getHandlers(allHandlers, type);
    return (
        <Card className="d-flex flex-column m-0 p-3" style={{ gap: "1rem", maxWidth: "992px" }}>
            <div className="align-items-end d-flex justify-content-end mb-n2">
                {handlers.handleSkip && (
                    <DataCardSkipButton 
                        cardData={cardData}
                        fn={handlers.handleSkip}
                    />
                )}
                {handlers.handleAdjudicate && (
                    <DataCardAdjudicateButton
                        cardData={cardData}
                        fn={handlers.handleAdjudicate}
                    />
                )} 
            </div>
            <DataCardText cardData={cardData} />
            <DataCardMetadata cardData={cardData} />
            {labels && handlers.handleSelectLabel && (
                <Fragment>
                    {labels.labels.length <= 5 ? (
                        <DataCardLabelButtons
                            cardData={cardData}
                            fn={handlers.handleSelectLabel}
                        />
                    ) : (
                        <Fragment>
                            <DataCardSuggestedLabels
                                cardData={cardData}
                                fn={handlers.handleSelectLabel}
                            />
                            <DataCardSelectLabel
                                cardData={cardData}
                                fn={handlers.handleSelectLabel}
                            />
                        </Fragment>
                    )}
                </Fragment>
            )}
        </Card>
    );
};

export const PAGES = {
    ANNOTATE_DATA: 0,
    HISTORY: 1,
    SKEW: 2,
    ADMIN: 3,
    RECYCLE: 4,
};

// currently rendering components based on if handler function is null, but this might be more readable
// const components = {
//     ADJUDICATE: [PAGES.ANNOTATE_DATA, PAGES.HISTORY, PAGES.SKEW],
//     SKIP: [PAGES.ANNOTATE_DATA],
//     TEXT: "all",
//     METADATA: "all",
//     LABELS: [PAGES.ANNOTATE_DATA, PAGES.HISTORY, PAGES.SKEW, PAGES.ADMIN]
// }

// when all actions are hooks, this logic can be transferred to hooks.
// the hooks will take in the page and determine the function
const getHandlers = (fns, page) => {
    switch (page) {
    case PAGES.ANNOTATE_DATA:
        return {
            handleSelectLabel: fns.actions.onSelectLabel,
            handleAdjudicate: fns.actions.onAdjudicate,
            handleSkip: fns.actions.onSkip,
        };
    case PAGES.HISTORY:
        return {
            handleSelectLabel: fns.modifyLabel,
            handleAdjudicate: fns.changeToSkip,
            handleSkip: null,
        };
    case PAGES.SKEW:
        break;
    case PAGES.ADMIN:
        break;
    case PAGES.RECYCLE:
        break;
    default:
        break;
    }
};

const formatDataForCard = (item, page) => {
    // should use defaultData with spread because es-lint doesn't like it
    const defaultData = {
        dataID: null,
        labelID: null,
        text: null,
        metadata: null,
        start_time: null,
        num_cards_left: null,
        is_admin: window.ADMIN,
    };
    switch (page) {
    case PAGES.ANNOTATE_DATA:
        return {
            ...defaultData,
            dataID: item.text.pk,
            text: item.text.text,
            metadata: item.text.metadata,
            start_time: item.start_time,
            num_cards_left: item.num_cards_left,
        };
    case PAGES.HISTORY:
        return {
            ...defaultData,
            dataID: item.id,
            labelID: item.labelID,
            text: item.data,
            metadata: item.metadata,
        };
    case PAGES.SKEW:
        break;
    case PAGES.ADMIN:
        break;
    case PAGES.RECYCLE:
        break;
    default:
        break;
    }
};

export default DataCard;
