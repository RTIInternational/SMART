import React from 'react';
import { connect } from 'react-redux';

import { fetchCards, annotateCard, passCard } from '../actions/card';
import Card from '../components/card';

const PROJECT_ID = window.PROJECT_ID;

const CardContainer = (props) => <Card {...props} />;

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
        passCard: (dataID, num_cards_left, is_admin) => {
            dispatch(passCard(dataID, num_cards_left, is_admin, PROJECT_ID));
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(CardContainer);
