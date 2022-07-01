import React from 'react';
import { connect } from 'react-redux';

import { fetchCards, annotateCard, passCard } from '../actions/card';
import DataCard from '../components/DataCard';

const PROJECT_ID = window.PROJECT_ID;

const CardContainer = (props) => <DataCard {...props} />;

const mapStateToProps = (state) => {
    return {
        cards: state.card.cards,
        message: state.card.message,
        labels: state.card.labels
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        fetchCards: () => {
            dispatch(fetchCards(PROJECT_ID));
        },
        annotateCard: (dataID, labelID, num_cards_left, is_admin) => {
            dispatch(annotateCard(dataID, labelID, num_cards_left, PROJECT_ID, is_admin));
        },
        passCard: (dataID, num_cards_left, is_admin, addToAdminQueue, message) => {
            dispatch(passCard(dataID, num_cards_left, is_admin, PROJECT_ID, addToAdminQueue, message));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(CardContainer);
