import React, { Fragment } from "react";
import { Card, ButtonToolbar } from "react-bootstrap";

import DataCardAdjudicateButton from "./DataCardAdjudicateButton";
import DataCardSkipButton from "./DataCardSkipButton";
import DataCardMetadata from "./DataCardMetadata";
import DataCardSelectLabel from "./DataCardSelectLabel";
import DataCardSuggestedLabels from "./DataCardSuggestedLabels";
import DataCardText from "./DataCardText";
import { useModifyLabel, useChangeToSkip, useLabels } from "../../hooks";
import DataCardLabelButtons from "./DataCardLabelButtons";
import DataCardDiscardButton from "./DataCardDiscardButton";

const DataCard = ({ data, page, actions }) => {
    const { data: labels } = useLabels();
    const { mutate: changeToSkip } = useChangeToSkip();
    const { mutate: modifyLabel } = useModifyLabel();
    const allHandlers = {
        changeToSkip,
        modifyLabel,
        actions,
    };
    const cardData = formatDataForCard(data, page);
    const handlers = getHandlers(allHandlers, page);

    const labelCountLow = (labels) => labels.labels.length <= 5;

    const show = {
        skipButton: handlers.handleSkip != null,
        adjudicateButton: handlers.handleAdjudicate != null,
        text: true,
        metadata: true,
        metadataEdit: page !== PAGES.RECYCLE,
        labelButtons: labels && labelCountLow(labels) && handlers.handleSelectLabel != null,
        labelSuggestions: labels && !labelCountLow(labels) && handlers.handleSelectLabel != null,
        labelSelect: labels && !labelCountLow(labels) && handlers.handleSelectLabel != null,
        discardButton: handlers.handleDiscard != null,
    };
    
    return (
        <Card className="d-flex flex-column m-0 p-3" style={{ gap: "1rem", maxWidth: "992px" }}>
            <div className="align-items-end d-flex justify-content-end mb-n2">
                { show.skipButton && (
                    <DataCardSkipButton 
                        cardData={cardData}
                        fn={handlers.handleSkip}
                    />
                )}
                { show.adjudicateButton && (
                    <DataCardAdjudicateButton
                        cardData={cardData}
                        fn={handlers.handleAdjudicate}
                    />
                )}
            </div>
            <DataCardText cardData={cardData} />
            <DataCardMetadata cardData={cardData} showEdit={show.metadataEdit} />
            {show.labelButtons && (        
                <ButtonToolbar>
                    <DataCardLabelButtons
                        cardData={cardData}
                        fn={handlers.handleSelectLabel}
                    />
                    <DataCardDiscardButton 
                        cardData={cardData} 
                        fn={handlers.handleDiscard} 
                        show={show.discardButton} 
                    />
                </ButtonToolbar>   

            )}
            {show.labelSuggestions && (
                <Fragment>
                    <DataCardSuggestedLabels
                        cardData={cardData}
                        fn={handlers.handleSelectLabel}
                    />
                    <div className="select-discard-wrapper" >
                        <div className="toolbar-gap" />
                        <DataCardSelectLabel
                            cardData={cardData}
                            fn={handlers.handleSelectLabel}
                        />
                        <DataCardDiscardButton 
                            cardData={cardData} 
                            fn={handlers.handleDiscard} 
                            show={show.discardButton}
                        />
                    </div>
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

// format incoming data based on calling tab
const formatDataForCard = (item, page) => {
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
        return {
            ...defaultData,
            dataID: item.id,
            text: item.data,
            metadata: item.metadata,
        };
    case PAGES.ADMIN:
        return {
            ...defaultData,
            dataID: item.id,
            text: item.data,
            metadata: item.metadata,
        };
    case PAGES.RECYCLE:
        return {
            ...defaultData,
            dataID: item.id,
            text: item.data,
            metadata: item.metadata,
        };
    default:
        break;
    }
};

// assign handlers based on page
// when all actions ported to react-query, this logic can be transferred to the react-query functions.
const getHandlers = (fns, page) => {
    switch (page) {
    case PAGES.ANNOTATE_DATA:
        return {
            handleSelectLabel: fns.actions.onSelectLabel,
            handleAdjudicate: fns.actions.onAdjudicate,
            handleSkip: fns.actions.onSkip,
            handleDiscard: null
        };
    case PAGES.HISTORY:
        return {
            handleSelectLabel: fns.modifyLabel,
            handleAdjudicate: fns.changeToSkip,
            handleSkip: null,
            handleDiscard: null
        };
    case PAGES.SKEW:
        return {
            handleSelectLabel: fns.actions.onSelectLabel,
            handleAdjudicate: null,
            handleSkip: null,
            handleDiscard: null
        };
    case PAGES.ADMIN:
        return {
            handleSelectLabel: fns.actions.onSelectLabel,
            handleAdjudicate: null,
            handleSkip: null,
            handleDiscard: fns.actions.onDiscard
        };
    case PAGES.RECYCLE:
        return {
            handleSelectLabel: null,
            handleAdjudicate: null,
            handleSkip: null,
            handleDiscard: null,
        };
    default:
        break;
    }
};

export default DataCard;
