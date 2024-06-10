import React from 'react';
import { connect } from 'react-redux';

import { fetchCards, annotateCard, passCard, unassignCard, modifyMetadataValues } from '../actions/card';
// import DataCard from '../components/DataCard';
import DataCard, { PAGES } from "../components/DataCard/DataCard";
// import DataCard from "../components/DataCard/DataCard";


const PROJECT_ID = window.PROJECT_ID;

const CardContainer = (props) => {
    React.useEffect(() => {
        if (props.cards.length === 0) {
            props.fetchCards();
        }
    }, [props.cards.length]);
    return (
        props.cards !== undefined && props.cards.length > 0 ? 
            <DataCard 
                data={{ ...props.cards[0], num_cards_left: props.cards.length }}
                page={PAGES.ANNOTATE_DATA} 
                actions={{ onSelectLabel: props.annotateCard, onAdjudicate: props.passCard, onSkip: props.unassignCard }} /> : null
    );
};


const mapStateToProps = (state) => {
    return {
        cards: state.card.cards,
        message: state.card.message,
        labels: state.smart.labels
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        fetchCards: () => {
            dispatch(fetchCards(PROJECT_ID));
        },
        annotateCard: ({ dataID, selectedLabelID, num_cards_left, start_time, is_admin }) => {
            dispatch(annotateCard(dataID, selectedLabelID, num_cards_left, start_time, PROJECT_ID, is_admin));
        },
        passCard: ({ dataID, num_cards_left, is_admin, message }) => {
            dispatch(passCard(dataID, num_cards_left, is_admin, PROJECT_ID, message));
        },
        unassignCard: ({ dataID, num_cards_left, is_admin }) => {
            dispatch(unassignCard(dataID, num_cards_left, is_admin, PROJECT_ID));
        },
        modifyMetadataValues: (dataPk, metadatas) => {
            dispatch(modifyMetadataValues(dataPk, metadatas, PROJECT_ID));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(CardContainer);
